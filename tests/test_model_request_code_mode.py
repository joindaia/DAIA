import copy
import json

import pytest

from daia.model_request import Denied, RequestGate


def encode(value):
    return json.dumps(value).encode()


def minimal_request():
    return {"model": "gpt-5.3-codex-spark", "store": False, "stream": True,
            "include": [], "tools": [],
            "input": [{"role": "user", "content": [{"type": "input_text", "text": "work"}]}]}


def code_mode_request():
    body = minimal_request()
    body["input"].insert(0, {
        "type": "additional_tools", "id": "at_original", "role": "developer",
        "tools": [{"type": "namespace", "name": "functions", "description": "local",
                   "tools": [
                       {"type": "custom", "name": "exec", "description": "local",
                        "format": {"type": "grammar", "syntax": "lark", "definition": "start: source"}},
                       {"type": "function", "name": "wait", "description": "local",
                        "parameters": {"type": "object"}, "strict": True},
                       {"type": "function", "name": "request_user_input", "description": "local",
                        "parameters": {"type": "object"}, "strict": True},
                   ]}],
    })
    return body


def test_original_minimal_spark_profile_is_unchanged():
    body = minimal_request()
    gate = RequestGate(encode(body))
    assert json.loads(gate.validate("POST", "/v1/responses", encode(body))) == body


@pytest.mark.parametrize("qualified", [True, False])
def test_native_catalog_and_custom_exec_pair_are_preserved(qualified):
    body = code_mode_request()
    gate = RequestGate(encode(body))
    body["input"][0]["id"] = "at_new_turn_id"
    body["input"].extend([
        {"type": "custom_tool_call", "id": "ctc_1", "status": "completed",
         "call_id": "call_1", "name": "exec", "namespace": "functions", "input": "{}"},
        {"type": "custom_tool_call_output", "id": "ctco_1", "call_id": "call_1",
         "output": [{"type": "input_text", "text": "done"}]},
    ])
    if not qualified:
        del body["input"][-2]["namespace"]
    forwarded = json.loads(gate.validate("POST", "/v1/responses", encode(body)))
    assert forwarded["input"][0]["tools"] == body["input"][0]["tools"]
    assert "id" not in forwarded["input"][0]
    assert forwarded["input"][-2]["name"] == "exec"
    assert ("namespace" in forwarded["input"][-2]) is qualified
    assert forwarded["input"][-1]["output"][0]["text"] == "done"


@pytest.mark.parametrize("mutate", [
    lambda body: body["input"][0]["tools"][0].update(description="changed"),
    lambda body: body["input"][0]["tools"][0]["tools"][0]["format"].update(definition="changed"),
    lambda body: body["input"][0]["tools"][0]["tools"].pop(),
    lambda body: body["input"].append(copy.deepcopy(body["input"][0])),
    lambda body: body["input"].pop(0),
    lambda body: body["input"][0]["tools"].append({"type": "mcp", "server_url": "https://example.org"}),
])
def test_catalog_changes_are_denied(mutate):
    approved = code_mode_request()
    gate = RequestGate(encode(approved))
    changed = copy.deepcopy(approved)
    mutate(changed)
    with pytest.raises(Denied):
        gate.validate("POST", "/v1/responses", encode(changed))


@pytest.mark.parametrize("item", [
    {"type": "custom_tool_call", "call_id": "c", "name": "wait",
     "namespace": "functions", "input": "{}"},
    {"type": "custom_tool_call", "call_id": "c", "name": "exec",
     "namespace": "remote", "input": "{}"},
    {"type": "custom_tool_call_output", "call_id": "c", "name": "unknown",
     "output": "done"},
])
def test_custom_calls_are_limited_to_approved_native_capabilities(item):
    body = code_mode_request()
    gate = RequestGate(encode(body))
    body["input"].append(item)
    with pytest.raises(Denied):
        gate.validate("POST", "/v1/responses", encode(body))


def test_custom_outputs_require_a_prior_matching_call():
    body = code_mode_request()
    gate = RequestGate(encode(body))
    body["input"].append({"type": "custom_tool_call_output", "call_id": "missing",
                          "output": "done"})
    with pytest.raises(Denied):
        gate.validate("POST", "/v1/responses", encode(body))

    body = code_mode_request()
    body["input"].extend([
        {"type": "custom_tool_call_output", "call_id": "call_1", "output": "done"},
        {"type": "custom_tool_call", "call_id": "call_1", "name": "exec",
         "namespace": "functions", "input": "{}"},
    ])
    with pytest.raises(Denied):
        RequestGate(encode(code_mode_request())).validate("POST", "/v1/responses", encode(body))


def test_custom_format_uses_supported_grammar_schema():
    for format in ({"type": "json", "syntax": "lark", "definition": "start: source"},
                   {"type": "grammar", "syntax": "javascript", "definition": "start: source"}):
        body = code_mode_request()
        body["input"][0]["tools"][0]["tools"][0]["format"] = format
        with pytest.raises(Denied):
            RequestGate(encode(body))


def test_custom_output_without_catalog_is_denied():
    body = minimal_request()
    body["input"].append({"type": "custom_tool_call", "call_id": "call_1",
                          "name": "exec", "namespace": "functions", "input": "{}"})
    body["input"].append({"type": "custom_tool_call_output", "call_id": "call_1",
                          "output": "done"})
    with pytest.raises(Denied):
        RequestGate(encode(body)).validate("POST", "/v1/responses", encode(body))


@pytest.mark.parametrize("other_namespace", [None, "other"])
def test_unqualified_exec_requires_unique_frozen_name(other_namespace):
    body = code_mode_request()
    other = copy.deepcopy(body["input"][0]["tools"][0]["tools"][0])
    body["tools"] = ([other] if other_namespace is None else
                     [{"type": "namespace", "name": other_namespace, "tools": [other]}])
    gate = RequestGate(encode(body))
    body["input"].append({"type": "custom_tool_call", "call_id": "call_1",
                          "name": "exec", "input": "text('fixture')"})
    with pytest.raises(Denied):
        gate.validate("POST", "/v1/responses", encode(body))


@pytest.mark.parametrize("fields", [
    {"name": "exec", "namespace": None},
    {"name": "functions.exec"},
    {"name": "exec", "namespace": "other"},
    {"name": "wait"},
])
def test_unqualified_alias_does_not_expand_custom_names(fields):
    body = code_mode_request(); gate = RequestGate(encode(body))
    body["input"].append({"type": "custom_tool_call", "call_id": "call_1",
                          "input": "text('fixture')", **fields})
    with pytest.raises(Denied):
        gate.validate("POST", "/v1/responses", encode(body))
