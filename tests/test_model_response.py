import json
import pytest
from daia.model_request import Denied, RequestGate
from daia.model_response import completed_output


def event(value):
    return b"data: " + json.dumps(value).encode() + b"\n\n"


def finish(items=None):
    return event({"type": "response.completed", "response": {
        "status": "completed", "output": items or []}})


def request():
    return {"model": "fixture", "store": False, "stream": True,
            "tools": [], "input": []}


ITEM = {"type": "reasoning", "id": "synthetic-item", "summary": [],
        "content": [], "encrypted_content": "synthetic-opaque-state"}


def test_realistic_completed_item_round_trip_and_cross_assignment_denial():
    wire = event({"type": "response.output_item.done", "item": ITEM}) + finish()
    gate = RequestGate(json.dumps(request()).encode())
    gate.record_provider_output(completed_output(wire))
    body = request(); body["input"] = [{k:v for k,v in ITEM.items() if k != "content"}]
    raw = json.dumps(body).encode()
    assert json.loads(gate.validate("POST", "/v1/responses", raw))["input"][0]["encrypted_content"] == ITEM["encrypted_content"]
    with pytest.raises(Denied):
        RequestGate(json.dumps(request()).encode()).validate("POST", "/v1/responses", raw)


def test_items_in_final_completion_are_also_returned():
    assert completed_output(finish([ITEM])) == [ITEM]


@pytest.mark.parametrize("suffix", [b"", b"data: not-json\n\n", finish()+event({"type":"response.created"}), finish()[:-1]])
def test_incomplete_or_invalid_stream_cannot_admit_earlier_reasoning(suffix):
    gate = RequestGate(json.dumps(request()).encode())
    with pytest.raises(Denied):
        gate.record_provider_output(completed_output(
            event({"type":"response.output_item.done","item":ITEM}) + suffix))
    body = request(); body["input"] = [{k:v for k,v in ITEM.items() if k != "content"}]
    with pytest.raises(Denied):
        gate.validate("POST", "/v1/responses", json.dumps(body).encode())


def test_invalid_completed_item_is_denied():
    with pytest.raises(Denied):
        completed_output(event({"type":"response.output_item.done","item":None})+finish())
