#!/usr/bin/env python3
"""Launcher script for the web-based branch description interface.

This script launches textual serve with the correct module path.
"""

import subprocess
import sys
import threading
import time
import webbrowser

import click


def launch_web_interface(port: int = 8000):
    """Launch the web interface using textual serve."""
    module_path = "dagster_dg_cli.cli_textual.empty_app:app"

    click.echo(f"🚀 Starting web interface on http://127.0.0.1:{port}")
    click.echo("The app will open in your browser...")
    click.echo("Press Ctrl+C to stop the server.")
    click.echo()

    # Start textual serve
    try:
        # Open browser after a short delay
        def open_browser():
            time.sleep(2)
            try:
                webbrowser.open(f"http://127.0.0.1:{port}")
            except Exception as e:
                click.echo(f"Could not auto-open browser: {e}")
                click.echo(f"Please manually visit: http://127.0.0.1:{port}")

        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()

        # Run textual serve
        subprocess.run(
            [sys.executable, "-m", "textual", "serve", module_path, "--port", str(port)],
            check=False,
        )

    except KeyboardInterrupt:
        click.echo("\n⚠️  Server stopped by user")
    except Exception as e:
        click.echo(f"❌ Error starting server: {e}")
        click.echo("Make sure textual is installed with: uv pip install 'textual[serve]'")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Launch web-based branch description interface")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")

    args = parser.parse_args()
    launch_web_interface(args.port)
