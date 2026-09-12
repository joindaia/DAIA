"""Optional official MCP Python SDK v2 adapter.

The static bearer verifier is for local development and an explicitly configured
private tailnet pilot only. It does not implement an
OAuth authorization server/login. Configure tokens in the host environment,
never in tool arguments. Public deployment requires the OIDC/OAuth milestone.
"""
from .service import Coordinator, Denied
from .http import BodyLimit
from urllib.parse import urlsplit
from pathlib import Path
import re
from contextvars import ContextVar

_gateway_agent = ContextVar("daia_gateway_agent", default=None)

from .crypto import strict_json


def pilot_origin(url: str) -> str:
    """Allow one exact MagicDNS endpoint, never a wildcard or public bind."""
    parsed = urlsplit(url)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or not parsed.hostname.endswith(".ts.net")
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path != "/mcp" or "*" in url):
        raise ValueError("Expected an exact http(s)://host.tailnet.ts.net[:port]/mcp URL")
    # Accessing port also rejects malformed/out-of-range ports.
    _ = parsed.port
    return f"{parsed.scheme}://{parsed.netloc}"


def load_allowed_agents(path: Path) -> frozenset[str]:
    """Read an operator-owned, bounded JSON allowlist; empty means deny all."""
    with path.open("rb") as source:
        raw = source.read(20001)
    if len(raw) > 20000:
        raise ValueError("Invalid agent allowlist")
    return validate_allowed_agents(strict_json(raw.decode("utf-8")))


def validate_allowed_agents(agents) -> frozenset[str]:
    if (not isinstance(agents, (list, set, frozenset, tuple)) or len(agents) > 256
            or any(not isinstance(a, str) or not re.fullmatch(r"[0-9a-f]{64}", a)
                   for a in agents) or len(set(agents)) != len(agents)):
        raise ValueError("Invalid agent allowlist")
    return frozenset(agents)


def build_mcp_app(service: Coordinator, *, tailnet_url: str | None = None,
                  allowed_agents: frozenset[str] | None = None,
                  certificate_agents: dict[str, str] | None = None):
    from mcp.server import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError
    from mcp.server.auth.provider import AccessToken, TokenVerifier
    from mcp.server.auth.settings import AuthSettings
    from mcp.server.auth.middleware.auth_context import get_access_token
    from pydantic import AnyHttpUrl
    from mcp.server.transport_security import TransportSecuritySettings

    if certificate_agents is not None:
        if not isinstance(certificate_agents, dict) or len(certificate_agents) > 256:
            raise ValueError("Invalid certificate policy")
        certificate_agents = dict(certificate_agents)
        validate_allowed_agents(list(certificate_agents))
        validate_allowed_agents(set(certificate_agents.values()))
        if allowed_agents is None:
            raise ValueError("Certificate mode requires explicit agent admission")
    if allowed_agents is not None:
        allowed_agents = validate_allowed_agents(allowed_agents)

    resource = tailnet_url or "http://127.0.0.1:8000/mcp"
    origins = ["http://127.0.0.1:8000", "http://localhost:8000"]
    hosts = ["127.0.0.1:*", "localhost:*"]
    if tailnet_url:
        origins.append(pilot_origin(tailnet_url))
        hosts.append(urlsplit(tailnet_url).netloc)

    class DevelopmentTokens(TokenVerifier):
        async def verify_token(self, token: str):
            try:
                root = service.authenticate(token)
                with service.store.connect() as db:
                    row = service._root(db, root)
                    expires = row["expires"]
                bound_agent = _gateway_agent.get() if certificate_agents is not None else None
                if certificate_agents is not None:
                    if bound_agent not in allowed_agents:
                        return None
                    with service.store.connect() as db:
                        service._agent(db, root, bound_agent)
                return AccessToken(token=token, client_id=("daia-cert:" + bound_agent if bound_agent else "daia-development-host"), subject=root,
                                   scopes=["work:contribute"], expires_at=expires, resource=resource)
            except Denied:
                return None

    server = MCPServer("DAIA development coordinator", token_verifier=DevelopmentTokens(),
                       log_level="WARNING",
                       auth=AuthSettings(issuer_url=AnyHttpUrl(resource.rsplit("/", 1)[0]),
                                         resource_server_url=AnyHttpUrl(resource),
                                         required_scopes=["work:contribute"],
                                         validate_token_resource=True))

    def root(agent_id: str | None = None):
        access = get_access_token()
        if access is None or not access.subject:
            raise Denied("Authenticated contributor required")
        if allowed_agents is not None and agent_id not in allowed_agents:
            raise ToolError("Agent not admitted")
        if certificate_agents is not None and access.client_id != "daia-cert:" + str(agent_id):
            raise ToolError("Agent not admitted")
        return access.subject

    if allowed_agents is None:
        @server.tool()
        async def registration_challenge(public_key: str) -> dict:
            """Request a short-lived Ed25519 possession challenge. Never send a private key."""
            return service.challenge(root(), public_key)

        @server.tool()
        async def register_agent(challenge_id: str, signature: str) -> dict:
            """Register by signing the challenge locally. Authentication binds the owner."""
            return service.register(root(), challenge_id, signature)

    @server.tool()
    async def contribution_status(agent_id: str) -> dict:
        """Inspect your grant and recover your live lease without claiming new work."""
        return service.contribution_status(root(agent_id), agent_id)

    @server.tool()
    async def request_work(agent_id: str) -> dict:
        """Obtain scheduler-assigned work. No job, target, or review-mode selection."""
        return service.request_work(root(agent_id), agent_id)

    @server.tool()
    async def heartbeat(agent_id: str, assignment_id: str) -> dict:
        """Renew an owned lease without extending its fixed hard deadline."""
        return service.heartbeat(root(agent_id), agent_id, assignment_id)

    @server.tool()
    async def release_work(agent_id: str, assignment_id: str) -> dict:
        """Decline unsafe/unwanted work. Exposure history remains; no forced execution."""
        return service.release(root(agent_id), agent_id, assignment_id)

    @server.tool()
    async def submission_envelope(agent_id: str, assignment_id: str, artifact: str, verdict: str) -> dict:
        """Prepare an envelope. Compare it with your lease and artifact before signing locally."""
        return service.envelope(root(agent_id), agent_id, assignment_id, artifact, verdict)

    @server.tool()
    async def submit_result(agent_id: str, assignment_id: str, artifact: str, verdict: str, signature: str) -> dict:
        """Submit signed evidence for your assignment. A submitted pass is not certification."""
        return service.submit(root(agent_id), agent_id, assignment_id, artifact, verdict, signature)

    # Serving this app at the root preserves its built-in lifespan and /mcp route.
    app = BodyLimit(server.streamable_http_app(
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True, allowed_hosts=hosts, allowed_origins=origins),
        max_request_body_size=16384,
    ), allowed_origins=origins)

    if certificate_agents is None:
        return app

    async def certificate_boundary(scope, receive, send):
        if scope["type"] != "http":
            return await app(scope, receive, send)
        # Uvicorn Unix sockets have no IP peer. Filesystem connect permissions are
        # still mandatory: this header is an assertion by the trusted gateway.
        headers = [value for key, value in scope.get("headers", [])
                   if key.lower() == b"x-daia-client-cert-sha256"]
        fingerprint = headers[0].decode("ascii", errors="replace") if len(headers) == 1 else ""
        agent = certificate_agents.get(fingerprint)
        if scope.get("client") is not None or agent is None:
            await send({"type": "http.response.start", "status": 403,
                        "headers": [(b"content-type", b"text/plain")]})
            await send({"type": "http.response.body", "body": b"Forbidden"})
            return
        token = _gateway_agent.set(agent)
        try:
            await app(scope, receive, send)
        finally:
            _gateway_agent.reset(token)

    return certificate_boundary
