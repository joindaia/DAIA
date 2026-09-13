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
            _require(all(type(t) is dict and t.get("type") == "function" for t in children))
            _local_tools(children)
        else:
            _require(kind == "function")
            _require(set(tool) <= {"type", "name", "description", "parameters", "strict"})
            _require(type(tool.get("name")) is str)
            _require(type(tool.get("parameters")) is dict)


def _text_blocks(value) -> None:
    _require(type(value) is list)
    for part in value:
        _require(type(part) is dict and set(part) == {"type", "text"})
        _require(part["type"] in ("input_text", "output_text") and type(part["text"]) is str)


def _history(items, admitted_reasoning=frozenset()) -> None:
    _require(type(items) is list)
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
        elif kind == "function_call":
            _require(set(item) <= {"type", "name", "namespace", "call_id", "arguments"})
            _require(all(type(item.get(k)) is str for k in ("name", "call_id", "arguments")))
            _require("namespace" not in item or type(item["namespace"]) is str)
        elif kind == "function_call_output":
            _require(set(item) == {"type", "call_id", "output"})
            _require(type(item["call_id"]) is str)
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
    """

    def __init__(self, approved_template: bytes):
        body = _decode(approved_template)
        _require(set(body) <= {"model", "instructions", "input", "tools", "tool_choice",
                              "parallel_tool_calls", "reasoning", "store", "stream",
                              "include", "prompt_cache_key", "text", "client_metadata"})
        _require(type(body.get("model")) is str and bool(body["model"]))
        _require(body.get("store") is False and body.get("stream") is True)
        _local_tools(body.get("tools"))
        _require(body.get("include", []) in ([], ["reasoning.encrypted_content"]))
        _history(body.pop("input", []))
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
        history = body.pop("input", None)
        _history(history, self._reasoning)
        _require(json.dumps(body, sort_keys=True, allow_nan=False) == self._template)
        # Forward only validated inline history, with optional item IDs removed.
        body["input"] = history
        return json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
