# serve_app.py
from textual_serve.server import Server  # type: ignore

# Launch the same BranchDescriptionApp as the terminal version using the module path
server = Server(
    "python -m dagster_dg_cli.cli_textual.branch_description_app",
    port=8000,
    host="localhost",
)

if __name__ == "__main__":
    server.serve(debug=True)
