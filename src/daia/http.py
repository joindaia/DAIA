"""Local development REST adapter, not an internet-ready authorization server."""
from typing import Literal
from fastapi import FastAPI, Depends, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .service import Coordinator, Denied

class BodyLimit:
    def __init__(self, app, maximum=16384, allowed_origins=None):
        self.app, self.maximum = app, maximum
        self.allowed_origins = {origin.encode("ascii") for origin in (
            allowed_origins or ("http://127.0.0.1:8000", "http://localhost:8000"))}

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        origins = [value for key, value in scope.get("headers", []) if key.lower() == b"origin"]
        if origins and (len(origins) != 1 or origins[0] not in self.allowed_origins):
            return await JSONResponse({"error": "origin_denied"}, 403)(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > self.maximum:
                return await JSONResponse({"error": "body_too_large"}, 413)(scope, receive, send)
            body.extend(chunk)
            if not message.get("more_body", False):
                break
        replayed = False
        async def buffered_receive():
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()
        await self.app(scope, buffered_receive, send)

class StrictBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

class Challenge(StrictBody):
    public_key: str = Field(pattern=r"^[0-9a-f]{64}$")

class Registration(StrictBody):
    challenge_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    signature: str = Field(pattern=r"^[0-9a-f]{128}$")

class Agent(StrictBody):
    agent_id: str = Field(pattern=r"^[0-9a-f]{64}$")

class Lease(Agent):
    assignment_id: str = Field(pattern=r"^[0-9a-f]{32}$")

class Evidence(Lease):
    artifact: str = Field(max_length=4096)
    verdict: Literal["candidate", "pass", "fail", "inconclusive"]

class Submission(Evidence):
    signature: str = Field(pattern=r"^[0-9a-f]{128}$")


def create_app(service: Coordinator) -> FastAPI:
    app = FastAPI(title="DAIA development coordinator", version="0.1.0",
                  docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(BodyLimit)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]"])
    bearer = HTTPBearer(auto_error=False)

    def principal(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise Denied("Unauthorized")
        return service.authenticate(credentials.credentials)

    @app.exception_handler(Denied)
    async def denied(request: Request, exc: Denied):
        # No raw tokens, input fields, file paths, or traceback in error responses.
        return JSONResponse({"error": "request_denied"}, status_code=403)

    @app.exception_handler(RequestValidationError)
    async def invalid(request: Request, exc: RequestValidationError):
        return JSONResponse({"error": "invalid_request"}, status_code=422)

    @app.get("/health")
    def health():
        return {"status": "development_only"}

    @app.get("/metrics")
    def metrics(root=Depends(principal)):
        return service.metrics()

    @app.post("/v1/registration/challenge")
    def challenge(body: Challenge, root=Depends(principal)):
        return service.challenge(root, body.public_key)

    @app.post("/v1/registration/complete")
    def register(body: Registration, root=Depends(principal)):
        return service.register(root, body.challenge_id, body.signature)

    @app.post("/v1/work/request")
    def request_work(body: Agent, root=Depends(principal)):
        return service.request_work(root, body.agent_id)

    @app.post("/v1/work/heartbeat")
    def heartbeat(body: Lease, root=Depends(principal)):
        return service.heartbeat(root, body.agent_id, body.assignment_id)

    @app.post("/v1/work/release")
    def release(body: Lease, root=Depends(principal)):
        return service.release(root, body.agent_id, body.assignment_id)

    @app.post("/v1/work/envelope")
    def envelope(body: Evidence, root=Depends(principal)):
        return service.envelope(root, body.agent_id, body.assignment_id, body.artifact, body.verdict)

    @app.post("/v1/work/submit")
    def submit(body: Submission, root=Depends(principal)):
        return service.submit(root, body.agent_id, body.assignment_id,
                              body.artifact, body.verdict, body.signature)
    return app
