import json
import random
import string
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional
from urllib import parse


def create_token_callback_handler(nonce: str) -> type[BaseHTTPRequestHandler]:
    class TokenCallbackHandler(BaseHTTPRequestHandler):
        def _send_shared_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "POST,OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def _error(self, code, message=None):
            self.send_error(code, message)
            self._send_shared_headers()
            self.end_headers()

        def do_OPTIONS(self):
            self.send_response(200)
            self._send_shared_headers()
            self.end_headers()

        def do_POST(self):
            url = parse.urlparse(self.path)

            if url.path != "/callback":
                self._error(404, "Page not found")
                return

            content = self.rfile.read(int(self.headers["Content-Length"]))
            body = json.loads(content)

            if not body.get("nonce") or body.get("nonce") != nonce:
                self._error(400, "Invalid nonce")
                return
            if not body.get("token"):
                self._error(400, "No user token provided")
                return
            if not body.get("organization"):
                self._error(400, "No organization provided")
                return

            organization = body.get("organization")
            token = body.get("token")

            self.send_response(200)
            self._send_shared_headers()
            response = b'{ "ok": true }'
            self.send_header("Content-length", str(len(response)))
            self.end_headers()

            self.wfile.write(response)

            # Pass back result values
            assert isinstance(self.server, TokenServer)
            self.server.set_result(organization=organization, token=token)
            self.server.shutdown()

        # Overridden so that the webserver doesn't log requests to the console

        def log_request(self, code="-", size="-"):
            return

    return TokenCallbackHandler


class TokenServer(HTTPServer):
    organization: Optional[str] = None
    token: Optional[str] = None

    def __init__(self, host: tuple[str, int], nonce: str):
        super().__init__(host, create_token_callback_handler(nonce))

    def shutdown(self):
        # Stop serving the token server
        # https://stackoverflow.com/a/36017741
        setattr(self, "_BaseServer__shutdown_request", True)

    def set_result(self, organization: str, token: str):
        self.organization = organization
        self.token = token

    def get_organization(self) -> Optional[str]:
        return self.organization

    def get_token(self) -> Optional[str]:
        return self.token


def _generate_nonce():
    return "".join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8)
    )


def start_login_server(base_url: Optional[str] = None) -> tuple[TokenServer, str]:
    """Starts a login server on a free port and returns
    the server and the URL to open in the browser.
    """
    from dagster_shared.utils import find_free_port

    port = find_free_port()
    nonce = _generate_nonce()
    escaped = parse.quote(f"/cli-auth/{nonce}?port={port}")
    auth_url = f"{base_url or 'https://dagster.cloud'}?next={escaped}"

    server = TokenServer(("localhost", port), nonce)
    return server, auth_url
