"""Optional official MCP Python SDK v2 adapter.

STATUS: scaffold, not runtime-tested in the offline bootstrap environment.
The static bearer verifier is LOCAL DEVELOPMENT ONLY. It does not implement an
OAuth authorization server/login. Configure tokens in the host environment,
never in tool arguments. Public deployment requires the OIDC/OAuth milestone.
"""
from .service import Coordinator, Denied
from .http import BodyLimit


def build_mcp_app(service: Coordinator):
    from mcp.server import MCPServer
    from mcp.server.auth.provider import AccessToken, TokenVerifier
    from mcp.server.auth.settings import AuthSettings
    from mcp.server.auth.middleware.auth_context import get_access_token
    from pydantic import AnyHttpUrl

    resource = "http://127.0.0.1:8000/mcp"

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
                       auth=AuthSettings(issuer_url=AnyHttpUrl("http://127.0.0.1:8000"),
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
    return BodyLimit(server.streamable_http_app())
