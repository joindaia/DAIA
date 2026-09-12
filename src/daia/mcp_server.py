"""Optional official MCP Python SDK v2 adapter.

The static bearer verifier is for local development and an explicitly configured
private tailnet pilot only. It does not implement an
OAuth authorization server/login. Configure tokens in the host environment,
never in tool arguments. Public deployment requires the OIDC/OAuth milestone.
"""
from .service import Coordinator, Denied
from .http import BodyLimit
from urllib.parse import urlsplit


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


def build_mcp_app(service: Coordinator, *, tailnet_url: str | None = None):
    from mcp.server import MCPServer
    from mcp.server.auth.provider import AccessToken, TokenVerifier
    from mcp.server.auth.settings import AuthSettings
    from mcp.server.auth.middleware.auth_context import get_access_token
    from pydantic import AnyHttpUrl
    from mcp.server.transport_security import TransportSecuritySettings

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
                return AccessToken(token=token, client_id="daia-development-host", subject=root,
                                   scopes=["work:contribute"], expires_at=expires, resource=resource)
            except Denied:
                return None

    server = MCPServer("DAIA development coordinator", token_verifier=DevelopmentTokens(),
                       log_level="WARNING",
                       auth=AuthSettings(issuer_url=AnyHttpUrl(resource.rsplit("/", 1)[0]),
                                         resource_server_url=AnyHttpUrl(resource),
                                         required_scopes=["work:contribute"],
                                         validate_token_resource=True))

    def root():
        access = get_access_token()
        if access is None or not access.subject:
            raise Denied("Authenticated contributor required")
        return access.subject

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
        return service.contribution_status(root(), agent_id)

    @server.tool()
    async def request_work(agent_id: str) -> dict:
        """Obtain scheduler-assigned work. No job, target, or review-mode selection."""
        return service.request_work(root(), agent_id)

    @server.tool()
    async def heartbeat(agent_id: str, assignment_id: str) -> dict:
        """Renew an owned lease without extending its fixed hard deadline."""
        return service.heartbeat(root(), agent_id, assignment_id)

    @server.tool()
    async def release_work(agent_id: str, assignment_id: str) -> dict:
        """Decline unsafe/unwanted work. Exposure history remains; no forced execution."""
        return service.release(root(), agent_id, assignment_id)

    @server.tool()
    async def submission_envelope(agent_id: str, assignment_id: str, artifact: str, verdict: str) -> dict:
        """Prepare an envelope. Compare it with your lease and artifact before signing locally."""
        return service.envelope(root(), agent_id, assignment_id, artifact, verdict)

    @server.tool()
    async def submit_result(agent_id: str, assignment_id: str, artifact: str, verdict: str, signature: str) -> dict:
        """Submit signed evidence for your assignment. A submitted pass is not certification."""
        return service.submit(root(), agent_id, assignment_id, artifact, verdict, signature)

    # Serving this app at the root preserves its built-in lifespan and /mcp route.
    return BodyLimit(server.streamable_http_app(
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True, allowed_hosts=hosts, allowed_origins=origins),
        max_request_body_size=16384,
    ), allowed_origins=origins)
