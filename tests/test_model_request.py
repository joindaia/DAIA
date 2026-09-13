"""Adversarial requests must fail before a caller could attach credentials."""
import json
import pytest
from daia.model_request import Denied, RequestGate


def encode(value):
    return json.dumps(value).encode()


def request():
    return {"model": "fixture", "store": False, "stream": True, "include": [],
            "tools": [{"type": "function", "name": "read", "parameters": {"type": "object"}}],
            "input": [{"role": "user", "content": [{"type": "input_text", "text": "Fix the test"}]}]}


def test_multi_turn_local_tool_history():
    original = request()
    gate = RequestGate(encode(original))
    for item in [
        {"type": "function_call", "name": "read", "call_id": "c1", "arguments": "{}"},
        {"type": "function_call_output", "call_id": "c1", "output": "test failed"},
        {"role": "assistant", "content": [{"type": "output_text", "text": "patch ready"}]},
    ]:
        original["input"].append(item)
        assert json.loads(gate.validate("POST", "/v1/responses", encode(original))) == original


@pytest.mark.parametrize("field,value", [
    ("previous_response_id", "another-session"), ("conversation", "personal"),
    ("store", True), ("background", True), ("model", "other"),
    ("tools", [{"type": "mcp", "server_url": "https://example.org"}]),
    ("include", ["reasoning.encrypted_content"]),
])
def test_reject_changed_authority(field, value):
    body = request(); gate = RequestGate(encode(body)); body[field] = value
    with pytest.raises(Denied): gate.validate("POST", "/v1/responses", encode(body))


@pytest.mark.parametrize("item", [
    {"type": "item_reference", "id": "personal-item"},
    {"role": "user", "content": [{"type": "input_file", "file_id": "personal-file"}]},
    {"role": "user", "content": [{"type": "input_image", "image_url": "https://example.org"}]},
    {"type": "reasoning", "encrypted_content": "unowned"},
])
def test_reject_resource_references(item):
    body = request(); gate = RequestGate(encode(body)); body["input"] = [item]
    with pytest.raises(Denied): gate.validate("POST", "/v1/responses", encode(body))


@pytest.mark.parametrize("raw", [b'{"store":false,"store":true}', b'{"v":NaN}',
                                b'{"v":1e999}', b'{} trailing', b'\xff', b'[' * 2000])
def test_ambiguous_or_invalid_json(raw):
    gate = RequestGate(encode(request()))
    with pytest.raises(Denied): gate.validate("POST", "/v1/responses", raw)


@pytest.mark.parametrize("path", ["/v1/responses?x=1", "/v1/responses/compact", "/connectors", "https://example.org/v1/responses"])
def test_only_fixed_route(path):
    with pytest.raises(Denied): RequestGate(encode(request())).validate("POST", path, encode(request()))


def test_hosted_tools_denied_even_in_template():
    body = request(); body["tools"] = [{"type": "web_search"}]
    with pytest.raises(Denied): RequestGate(encode(body))


def test_assignment_namespace_and_native_text_output():
    body = request()
    body['tools'] = [{'type': 'namespace', 'name': 'mcp__daia_assignment',
                      'description': 'Assigned helper', 'tools': body['tools']}]
    gate = RequestGate(encode(body))
    body['input'].append({'type': 'function_call_output', 'call_id': 'c2', 'output': [
        {'type': 'input_text', 'text': 'Wall time: 0.1\nOutput:'},
        {'type': 'input_text', 'text': '{"status":"already_recorded"}'}]})
    assert json.loads(gate.validate('POST', '/v1/responses', encode(body))) == body


def test_input_cannot_change_template_and_get_is_denied():
    body = request(); gate = RequestGate(encode(body))
    body['tools'][0]['name'] = 'different'
    with pytest.raises(Denied): gate.validate('POST', '/v1/responses', encode(body))
    with pytest.raises(Denied): gate.validate('GET', '/v1/responses', encode(request()))


def test_duplicate_key_in_otherwise_valid_request():
    body = request(); gate = RequestGate(encode(body))
    raw = encode(body).replace(b'"store": false', b'"store": true, "store": false')
    # A permissive last-key-wins parser would accept this exact approved profile.
    assert json.loads(raw) == body
    with pytest.raises(Denied): gate.validate('POST', '/v1/responses', raw)


@pytest.mark.parametrize('literal', [b'NaN', b'Infinity', b'-Infinity', b'1e999'])
def test_nonfinite_template_not_hidden_by_profile_mismatch(literal):
    body = request(); body['reasoning'] = {'effort': 12345}
    raw = encode(body).replace(b'12345', literal)
    with pytest.raises(Denied): RequestGate(raw)



def test_native_include_and_inline_ids_are_normalized():
    body = request(); body['include'] = ['reasoning.encrypted_content']
    body['input'][0]['id'] = 'msg_untrusted'
    gate = RequestGate(encode(body))
    cleaned = json.loads(gate.validate('POST', '/v1/responses', encode(body)))
    assert 'id' not in cleaned['input'][0]
    assert cleaned['input'][0]['content'] == body['input'][0]['content']
    body['input'] = [{'type': 'item_reference', 'id': 'msg_untrusted'}]
    with pytest.raises(Denied): gate.validate('POST', '/v1/responses', encode(body))
