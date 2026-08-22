from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .models import TargetManifest
from .oracle import interpret
from .verifier import verify_target

MAX_BODY_BYTES = 1_048_576


class TheaHandler(BaseHTTPRequestHandler):
    server_version = "Thea/0.1"

    def _json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "service": "thea-verifier",
                    "version": "0.1.0",
                    "authority_effect": "NONE",
                },
            )
            return
        self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/verify":
            self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return

        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            self._json(HTTPStatus.LENGTH_REQUIRED, {"error": "content_length_required"})
            return
        try:
            length = int(raw_length)
        except ValueError:
            self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid_content_length"})
            return
        if length < 1 or length > MAX_BODY_BYTES:
            self._json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "body_too_large"})
            return

        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("request body must be an object")
            target = TargetManifest.from_dict(payload)
            result = verify_target(target)
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid_manifest", "detail": str(exc)})
            return

        response: dict[str, object] = {"thea": result.to_dict()}
        if parse_qs(parsed.query).get("oracle") == ["1"]:
            response["oracle"] = interpret(result).to_dict()
        self._json(HTTPStatus.OK, response)

    def log_message(self, format: str, *args: object) -> None:
        # Request bodies and review evidence are intentionally not logged.
        print(f"[thea] {self.address_string()} {format % args}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve Thea on a bounded local HTTP interface")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="Explicit local port selected by the Operator; Thea does not self-register a canonical port.",
    )
    args = parser.parse_args()

    if args.host not in {"127.0.0.1", "::1", "localhost"}:
        raise SystemExit("Thea v0.1 refuses non-loopback binding; add an authenticated gateway before remote exposure.")
    if not 1 <= args.port <= 65535:
        raise SystemExit("port must be between 1 and 65535")

    server = ThreadingHTTPServer((args.host, args.port), TheaHandler)
    print(f"Thea v0.1 listening on loopback (authority_effect=NONE)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
