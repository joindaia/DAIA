"""Translate a trusted Nginx client certificate to the backend SHA-256 assertion.

Only for the private Unix socket. This does not verify a certificate chain: Nginx
must require and validate client certificates and overwrite the forwarded header.
"""
from urllib.parse import unquote_to_bytes
from cryptography import x509
from cryptography.hazmat.primitives import hashes


def certificate_bridge(app):
    async def wrapped(scope, receive, send):
        if scope["type"] != "http":
            return await app(scope, receive, send)
        headers = scope.get("headers", [])
        certificates = [v for k, v in headers if k.lower() == b"x-daia-client-cert"]
        try:
            if scope.get("client") is not None or len(certificates) != 1 or not 0 < len(certificates[0]) <= 8192:
                raise ValueError()
            pem = unquote_to_bytes(certificates[0]).strip()
            if (not pem.startswith(b"-----BEGIN CERTIFICATE-----")
                    or not pem.endswith(b"-----END CERTIFICATE-----")
                    or pem.count(b"-----BEGIN CERTIFICATE-----") != 1):
                raise ValueError()
            fingerprint = x509.load_pem_x509_certificate(pem).fingerprint(hashes.SHA256()).hex().encode("ascii")
        except (ValueError, TypeError):
            await send({"type": "http.response.start", "status": 403,
                        "headers": [(b"content-type", b"text/plain")]})
            await send({"type": "http.response.body", "body": b"Forbidden"})
            return
        forwarded = [(k, v) for k, v in headers if k.lower() not in
                     {b"x-daia-client-cert", b"x-daia-client-cert-sha256"}]
        forwarded.append((b"x-daia-client-cert-sha256", fingerprint))
        await app({**scope, "headers": forwarded}, receive, send)
    return wrapped
