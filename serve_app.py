# serve_app.py
from textual_serve.server import Server

server = Server("python -m dagster_dg_cli.cli_textual.web_branch_app", port=8000)
server.serve(debug=True)
