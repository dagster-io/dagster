import json
import random
import string
import webbrowser
from enum import Enum
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional
from urllib import parse

from typer import Argument, Context, Option, Typer

from .. import gql, ui
from ..config_utils import (
    DagsterCloudCliConfig,
    available_deployment_names,
    dagster_cloud_options,
    read_config,
    write_config,
)
from ..utils import find_free_port

app = Typer(help="Configure the Dagster Cloud CLI.")


@app.command()
@dagster_cloud_options()
def set_deployment(
    ctx: Context,
    deployment: str = Argument(..., autocompletion=available_deployment_names),
):
    """Set the default deployment for CLI commands."""
    deployments = available_deployment_names(ctx=ctx)
    if not deployment or deployment not in deployments:
        raise ui.error(f"Deployment {ui.as_code(deployment)} not found")

    config = read_config()
    new_config = config._replace(default_deployment=deployment)
    write_config(new_config)

    ui.print(f"Default deployment changed to {ui.as_code(deployment)}")


@app.command()
def view(
    show_token: bool = Option(
        False,
        "--show-token",
        "-s",
        help="Whether to display the user token in plaintext.",
    ),
):
    """View the current CLI configuration."""
    config = read_config()
    if not show_token and config.user_token:
        config = config._replace(user_token=ui.censor_token(config.user_token))
    config_to_display = {k: v for k, v in config._asdict().items() if v is not None}
    ui.print_yaml(config_to_display)


app_configure = Typer()


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


class SetupAuthMethod(Enum):
    WEB = "web"
    CLI = "cli"


def _settings_method_input(api_token: str):
    if api_token:
        choices = [
            ui.choice(SetupAuthMethod.CLI, "Authenticate using token or keep current settings"),
            ui.choice(SetupAuthMethod.WEB, "Authenticate in browser"),
        ]
    else:
        choices = [
            ui.choice(SetupAuthMethod.WEB, "Authenticate in browser"),
            ui.choice(SetupAuthMethod.CLI, "Authenticate using token"),
        ]
    return ui.list_input(
        "How would you like to authenticate the CLI?",
        choices,
    )


def _generate_nonce():
    return "".join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8)
    )


def _setup(organization: str, deployment: str, api_token: str):
    setup_method = _settings_method_input(api_token)

    if setup_method == SetupAuthMethod.WEB:
        port = find_free_port()
        nonce = _generate_nonce()
        escaped = parse.quote(f"/cli-auth/{nonce}?port={port}")
        auth_url = f"https://dagster.cloud?next={escaped}"
        try:
            webbrowser.open(auth_url, new=0, autoraise=True)
            ui.print(
                f"Opening browser...\nIf a window does not open automatically, visit {auth_url} to"
                " finish authorization"
            )
        except webbrowser.Error as e:
            ui.warn(
                f"Error launching web browser: {e}\n\nTo finish authorization, visit {auth_url}\n"
            )

        server = TokenServer(("localhost", port), nonce)
        server.serve_forever()
        new_org = server.get_organization()
        new_api_token = server.get_token()
        ui.print(f"Authorized for organization {ui.as_code(str(new_org))}\n")
    else:
        new_org = ui.input("Dagster Cloud organization:", default=organization or "") or None
        if not api_token:
            deployment_name = deployment if deployment else "prod"
            ui.print(
                "\nTo create a new user token or find an existing token, visit"
                f" https://dagster.cloud/{new_org}/{deployment_name}/org-settings/tokens"
            )
        new_api_token = (
            ui.password_input("Dagster Cloud user token:", default=api_token or "") or None
        )

    # Attempt to fetch deployment names from server, fallback to a text input upon failure
    deployment_names = []
    if new_org and new_api_token:
        try:
            with gql.graphql_client_from_url(gql.url_from_config(new_org), new_api_token) as client:
                deployments = gql.fetch_full_deployments(client)
            deployment_names = [deployment["deploymentName"] for deployment in deployments]
        except:
            ui.warn(
                "Could not fetch deployment names from server - organization or user token may be"
                " set incorrectly."
            )

    new_deployment: Optional[str] = None
    if deployment_names:
        options = ["None"] + deployment_names
        new_deployment = ui.list_input(
            "Default deployment:",
            choices=options,
            default=deployment if deployment in options else "None",
        )
        if new_deployment == "None":
            new_deployment = None
    else:
        new_deployment = ui.input("Default deployment:", default=deployment or "") or None

    write_config(
        DagsterCloudCliConfig(
            organization=new_org,
            default_deployment=new_deployment,
            user_token=new_api_token,
        )
    )


@app.command()
@dagster_cloud_options(allow_empty=True)
def setup(organization: str, deployment: str, api_token: str):
    """Populate the CLI configuration."""
    _setup(organization, deployment, api_token)


app_configure = Typer(hidden=True)


# Legacy, to support the old `dagster-cloud configure` path
# New command is `dagster-cloud config setup`
@app_configure.command(name="configure", hidden=True)
@dagster_cloud_options(allow_empty=True)
def configure_legacy(organization: str, deployment: str, api_token: str):
    """Populate the CLI configuration."""
    _setup(organization, deployment, api_token)
