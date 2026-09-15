"""Experimental text-only Responses gate, for use outside an untrusted worker.

No networking, credentials or provider compatibility claim. The trusted controller
supplies a frozen request template; only explicit text/tool history may vary.
Unknown representations fail closed. This is not a complete credential proxy.
"""
from __future__ import annotations

import json
import hashlib


class Denied(ValueError):
    """Request cannot be forwarded under this assignment's frozen profile."""


def _require(condition: bool) -> None:
    if not condition:
        raise Denied("model request outside assignment profile")


def _pairs(items):
    result = {}
    for key, value in items:
        _require(key not in result)
        result[key] = value
    return result


def _constant(_):
    raise Denied("nonfinite JSON")


def _decode(raw: bytes) -> dict:
    _require(type(raw) is bytes and 0 < len(raw) <= 1024 * 1024)
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                           parse_constant=_constant)
        # Also rejects floating-point overflow, not just literal Infinity/NaN.
        json.dumps(value, allow_nan=False)
    except (ValueError, UnicodeError, RecursionError, OverflowError) as exc:
        raise Denied("invalid model JSON") from exc
    _require(type(value) is dict)
    return value


def _local_tools(tools: list) -> None:
    _require(type(tools) is list)
    for tool in tools:
        _require(type(tool) is dict)
        kind = tool.get("type")
        if kind == "namespace":
            _require(set(tool) <= {"type", "name", "description", "tools"})
            _require(type(tool.get("name")) is str)
            children = tool.get("tools")
            _require(type(children) is list)
            _require(all(type(t) is dict and t.get("type") in ("function", "custom")
                         for t in children))
            _local_tools(children)
        elif kind == "function":
            _require(set(tool) <= {"type", "name", "description", "parameters", "strict"})
            _require(type(tool.get("name")) is str)
            _require(type(tool.get("parameters")) is dict)
        else:
            _require(kind == "custom")
            _require(set(tool) == {"type", "name", "description", "format"})
            _require(type(tool["name"]) is str and type(tool["description"]) is str)
            format = tool["format"]
            _require(type(format) is dict and set(format) == {"type", "syntax", "definition"})
            _require(format["type"] == "grammar" and format["syntax"] in ("lark", "regex"))
            _require(type(format["definition"]) is str)


def _text_blocks(value) -> None:
    _require(type(value) is list)
    for part in value:
        _require(type(part) is dict and set(part) == {"type", "text"})
        _require(part["type"] in ("input_text", "output_text") and type(part["text"]) is str)


def _tool_names(tools, namespace=None):
    names = set()
    for tool in tools:
        if tool["type"] == "namespace":
            names.update(_tool_names(tool["tools"], tool["name"]))
        else:
            names.add((namespace, tool["name"]))
    return names


def _additional_tools(item):
    _require(type(item) is dict)
    if "id" in item:
        _require(type(item["id"]) is str)
    clean = dict(item)
    clean.pop("id", None)
    _require(set(clean) == {"type", "role", "tools"})
    _require(clean["type"] == "additional_tools" and clean["role"] == "developer")
    _local_tools(clean["tools"])
    return json.dumps(clean, sort_keys=True, allow_nan=False), _tool_names(clean["tools"])


def _input_catalog(items):
    _require(type(items) is list)
    catalogs = [item for item in items if isinstance(item, dict)
                and item.get("type") == "additional_tools"]
    _require(len(catalogs) <= 1)
    if not catalogs:
        return None, None
    catalog, names = _additional_tools(catalogs[0])
    return catalog, frozenset(names)


def _history(items, admitted_reasoning=frozenset(), approved_names=None,
             approved_catalog=None, *, unqualified_exec=False) -> None:
    _require(type(items) is list)
    custom_calls = {}
    for item in items:
        _require(type(item) is dict)
        # Full inline items need no provider-side lookup. Remove optional IDs
        # rather than forwarding an untrusted cross-session identifier.
        if "id" in item:
            _require(type(item["id"]) is str)
            del item["id"]
        kind = item.get("type", "message")
        if kind == "message":
            _require(set(item) <= {"type", "role", "content", "phase"})
            if "phase" in item:
                _require(item.get("role") == "assistant" and
                         item["phase"] in ("commentary", "final_answer"))
            _require(item.get("role") in ("system", "developer", "user", "assistant"))
            _text_blocks(item.get("content"))
        elif kind == "reasoning":
            _require(_reasoning_digest(item) in admitted_reasoning)
        elif kind == "additional_tools":
            _require(approved_catalog is not None)
            catalog, _ = _additional_tools(item)
            _require(catalog == approved_catalog)
        elif kind == "function_call":
            _require(set(item) <= {"type", "name", "namespace", "call_id", "arguments"})
            _require(all(type(item.get(k)) is str for k in ("name", "call_id", "arguments")))
            _require("namespace" not in item or type(item["namespace"]) is str)
            if approved_names is not None:
                _require((item.get("namespace"), item["name"]) in approved_names)
        elif kind == "function_call_output":
            _require(set(item) == {"type", "call_id", "output"})
            _require(type(item["call_id"]) is str)
            if type(item["output"]) is not str:
                _text_blocks(item["output"])
        elif kind == "custom_tool_call":
            _require(set(item) <= {"type", "status", "call_id", "name", "namespace", "input"})
            _require(set(item) >= {"type", "call_id", "name", "input"})
            _require(item["name"] == "exec")
            _require(item.get("namespace") == "functions" or
                     "namespace" not in item and unqualified_exec)
            _require(item.get("status") in (None, "completed", "in_progress"))
            _require(all(type(item[k]) is str for k in ("call_id", "name", "input")))
            _require(approved_names is not None and ("functions", "exec") in approved_names)
            _require(item["call_id"] not in custom_calls)
            custom_calls[item["call_id"]] = item["name"]
        elif kind == "custom_tool_call_output":
            _require(set(item) <= {"type", "call_id", "name", "output"})
            _require(set(item) >= {"type", "call_id", "output"})
            _require(type(item["call_id"]) is str and approved_names is not None)
            _require(item["call_id"] in custom_calls)
            if "name" in item:
                _require(type(item["name"]) is str and item["name"] == custom_calls[item["call_id"]])
            custom_calls.pop(item["call_id"])
            if type(item["output"]) is not str:
                _text_blocks(item["output"])
        else:
            # Includes item_reference, file/image inputs and opaque reasoning state.
            raise Denied("unsupported input representation")


def _reasoning_digest(item):
    _require(set(item) == {"type", "summary", "encrypted_content"})
    _require(item.get("type") == "reasoning")
    _require(type(item["encrypted_content"]) is str and bool(item["encrypted_content"]))
    _require(type(item["summary"]) is list)
    for part in item["summary"]:
        _require(type(part) is dict and set(part) == {"type", "text"})
        _require(part["type"] == "summary_text" and type(part["text"]) is str)
    raw = json.dumps(item, sort_keys=True, allow_nan=False).encode()
    _require(len(raw) <= 1024 * 1024)
    return hashlib.sha256(raw).digest()


class RequestGate:
    """Freeze approved non-history fields as bytes; never learn policy from a job.

    Caller must authorize the template independently, not take the first guest
    request as approval. Trusted template values are also restricted here so it
    cannot accidentally enable hosted tools or remote response references.
    Native client_metadata and prompt_cache_key are discarded from both sides;
    they never become provider inputs or authorization fields.
    """

    def __init__(self, approved_template: bytes):
        body = _decode(approved_template)
        for field in ("client_metadata", "prompt_cache_key"):
            body.pop(field, None)
        _require(set(body) <= {"model", "instructions", "input", "tools", "tool_choice",
                              "parallel_tool_calls", "reasoning", "store", "stream",
                              "include", "text"})
        _require(type(body.get("model")) is str and bool(body["model"]))
        _require(body.get("store") is False and body.get("stream") is True)
        if "tools" in body:
            _local_tools(body["tools"])
        _require(body.get("include", []) in ([], ["reasoning.encrypted_content"]))
        input_items = body.pop("input", [])
        self._catalog, self._approved_names = _input_catalog(input_items)
        # Native Codex also records bare exec. Resolve it only when the frozen
        # top-level and deferred declarations cannot refer to another exec.
        names = _tool_names(body.get("tools", [])) | (self._approved_names or frozenset())
        self._unqualified_exec = {pair for pair in names if pair[1] == "exec"} == {("functions", "exec")}
        _history(input_items, approved_names=self._approved_names,
                 approved_catalog=self._catalog, unqualified_exec=self._unqualified_exec)
        self._template = json.dumps(body, sort_keys=True, allow_nan=False)
        self._reasoning = set()

    def record_provider_output(self, items: list) -> None:
        """Trusted caller only: output from a validated response for this binding.

        Never expose this method through a worker tool or learn from worker input.
        A fresh gate is required per assignment/account binding. This object is
        sequential: record the completed response before accepting the next turn.
        """
        _require(type(items) is list)
        admitted = set(self._reasoning)
        for item in items:
            _require(type(item) is dict)
            if item.get("type") == "reasoning":
                item = dict(item)
                if "id" in item:
                    _require(type(item.pop("id")) is str)
                if "content" in item:
                    _require(item.pop("content") in (None, []))
                admitted.add(_reasoning_digest(item))
        _require(len(admitted) <= 64)
        self._reasoning = admitted

    def validate(self, method: str, path: str, raw: bytes) -> bytes:
        """Return fresh canonical JSON, never the ambiguous original wire bytes.

        Fixed synthetic route for the first integration. HTTP framing, TLS,
        headers, credential injection, budgets and revocation are caller duties.
        """
        _require(method == "POST" and path == "/v1/responses")
        body = _decode(raw)
        # Native per-turn identifiers are neither authority nor upstream input.
        # Decode the entire request first, retaining duplicate/size/JSON checks.
        for field in ("client_metadata", "prompt_cache_key"):
            body.pop(field, None)
        history = body.pop("input", None)
        catalog, _ = _input_catalog(history)
        _require(catalog == self._catalog)
        _history(history, self._reasoning, self._approved_names, self._catalog,
                 unqualified_exec=self._unqualified_exec)
        _require(json.dumps(body, sort_keys=True, allow_nan=False) == self._template)
        # Forward only validated inline history, with optional item IDs removed.
        body["input"] = history
        return json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
