"""Read-only SDK handshake/tool-discovery probe. Never prints the invite token."""
import argparse
import asyncio
import json
from pathlib import Path

import httpx2
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def probe(invite):
    async with httpx2.AsyncClient(headers={"Authorization": "Bearer " + invite["token"]}, timeout=15) as http:
        async with streamable_http_client(invite["url"], http_client=http) as streams:
            async with ClientSession(streams[0], streams[1], read_timeout_seconds=15) as session:
                await session.initialize()
                names = sorted(tool.name for tool in (await session.list_tools()).tools)
                assert set(names) == {"registration_challenge", "register_agent", "contribution_status",
                                      "request_work", "heartbeat", "release_work",
                                      "submission_envelope", "submit_result"}
                print(json.dumps({"connection": "passed", "tools": names}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--invite", required=True, type=Path)
    args = parser.parse_args()
    asyncio.run(probe(json.loads(args.invite.read_text(encoding="utf-8"))))
