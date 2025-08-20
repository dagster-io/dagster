# serve_app.py
from textual_serve.server import Server

# The command should run your Textual app
server = Server("python -m dagster_dg_cli.cli_textual.web_branch_app", port=8000, host="localhost")

if __name__ == "__main__":
    server.serve(debug=True)
