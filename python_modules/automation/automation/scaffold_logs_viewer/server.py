import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


class ScaffoldBranchLogsHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, logs_directory: Path, **kwargs):
        self.logs_directory = logs_directory
        super().__init__(*args, **kwargs)

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == "/" or path == "/index.html":
            self._serve_index()
        elif path == "/api/sessions":
            self._serve_sessions_list()
        elif path.startswith("/api/sessions/"):
            filename = unquote(path.split("/")[-1])
            self._serve_session_data(filename)
        else:
            self._send_error(404, "Not found")

    def _serve_index(self):
        index_path = Path(__file__).parent / "index.html"
        try:
            with open(index_path) as f:
                content = f.read()
            self._send_response(200, content, "text/html")
        except Exception as e:
            self._send_error(500, f"Error serving index: {e}")

    def _serve_sessions_list(self):
        try:
            sessions = []
            for file_path in self.logs_directory.glob("scaffold_diagnostics_*.jsonl"):
                # Parse first line to get session info
                with open(file_path) as f:
                    first_line = f.readline().strip()
                    if first_line:
                        session_start = json.loads(first_line)
                        if session_start.get("type") == "session_start":
                            sessions.append(
                                {
                                    "filename": file_path.name,
                                    "correlation_id": session_start.get(
                                        "correlation_id", "unknown"
                                    ),
                                    "timestamp": session_start.get("timestamp", "unknown"),
                                }
                            )

            # Sort by timestamp descending (most recent first)
            sessions.sort(key=lambda x: x["timestamp"], reverse=True)

            self._send_json_response(sessions)
        except Exception as e:
            self._send_error(500, f"Error loading sessions: {e}")

    def _serve_session_data(self, filename: str):
        try:
            file_path = self.logs_directory / filename
            if not file_path.exists():
                self._send_error(404, "Session not found")
                return

            entries = []
            session_start = None

            with open(file_path) as f:
                for line_content in f:
                    stripped_line = line_content.strip()
                    if stripped_line:
                        entry = json.loads(stripped_line)
                        if entry.get("type") == "session_start":
                            session_start = entry
                        entries.append(entry)

            session_data = {
                "filename": filename,
                "correlation_id": session_start.get("correlation_id", "unknown")
                if session_start
                else "unknown",
                "start_time": session_start.get("timestamp", "unknown")
                if session_start
                else "unknown",
                "entries": entries,
            }

            self._send_json_response(session_data)
        except Exception as e:
            self._send_error(500, f"Error loading session data: {e}")

    def _send_response(self, status_code: int, content: str, content_type: str):
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.send_header("Content-Length", str(len(content.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def _send_json_response(self, data: Any):
        content = json.dumps(data, indent=2)
        self._send_response(200, content, "application/json")

    def _send_error(self, status_code: int, message: str):
        content = json.dumps({"error": message})
        self._send_response(status_code, content, "application/json")

    def log_message(self, format: str, *args):  # noqa: A002
        # Suppress default logging
        pass


def create_handler_class(logs_directory: Path):
    """Factory function to create handler class with logs directory bound."""

    class BoundHandler(ScaffoldBranchLogsHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, logs_directory=logs_directory, **kwargs)

    return BoundHandler


def serve_logs(logs_directory: Path, port: int = 8000, host: str = "localhost"):
    """Start the web server to browse scaffold branch logs."""
    handler_class = create_handler_class(logs_directory)

    with HTTPServer((host, port), handler_class) as httpd:
        import click

        click.echo(f"Serving scaffold logs viewer at http://{host}:{port}")
        click.echo(f"Logs directory: {logs_directory}")
        click.echo("Press Ctrl+C to stop")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            import click

            click.echo("\nShutting down server...")
