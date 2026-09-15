"""Parse a bounded completed provider stream before accepting opaque state.

Call only on responses authenticated by the fixed upstream binding. Parsing
alone neither authenticates the provider nor binds output to an assignment.
"""
from .model_request import Denied, _decode


def completed_output(output: bytes) -> list:
    """Collect completed items atomically; reject partial/malformed streams."""
    if type(output) is not bytes or not 0 < len(output) <= 8 * 1024 * 1024:
        raise Denied("invalid provider stream size")
    try:
        text = output.decode("utf-8").replace("\r\n", "\n")
    except UnicodeError:
        raise Denied("invalid provider stream") from None
    if not text.endswith("\n\n"):
        raise Denied("incomplete provider stream")
    completed = False
    items = []
    for block in text.split("\n\n"):
        if not block.strip():
            continue
        data, event = [], None
        for line in block.split("\n"):
            if line.startswith(":"):
                continue
            name, separator, value = line.partition(":")
            if not separator or name not in ("data", "event"):
                raise Denied("invalid provider event")
            value = value.removeprefix(" ")
            if name == "data":
                data.append(value)
            elif event is None:
                event = value
            else:
                raise Denied("duplicate provider event")
        if not data:
            if event is not None:
                raise Denied("missing provider event data")
            continue
        payload = "\n".join(data)
        if payload == "[DONE]" and completed and event is None:
            continue
        if completed:
            raise Denied("event after completion")
        value = _decode(payload.encode())
        kind = value.get("type")
        if (not isinstance(kind, str) or not kind.startswith("response.")
                or event is not None and event != kind):
            raise Denied("invalid provider event type")
        if kind == "response.output_item.done":
            item = value.get("item")
            if not isinstance(item, dict):
                raise Denied("invalid completed provider item")
            items.append(item)
        if kind == "response.completed":
            response = value.get("response", {})
            if (not isinstance(response, dict) or response.get("status") != "completed"
                    or not isinstance(response.get("output"), list)):
                raise Denied("invalid provider completion")
            items.extend(response["output"])
            completed = True
    if not completed:
        raise Denied("missing provider completion")
    return items
