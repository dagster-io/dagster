"""Hatch custom build hook for dagster-webserver.

Builds the frontend webapp when installing from source (e.g., git).
When webapp/build/ already exists (PyPI sdist/wheel), this is a no-op.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class WebappBuildHook(BuildHookInterface):
    PLUGIN_NAME = "webapp-builder"

    def initialize(self, version: str, build_data: dict) -> None:
        webapp_build = os.path.join(self.root, "dagster_webserver", "webapp", "build")

        if os.path.isfile(os.path.join(webapp_build, "index.html")):
            return  # Already built (PyPI install or prior build)

        # Locate the monorepo root by finding js_modules/
        js_modules = self._find_js_modules()
        if js_modules is None:
            print(
                "WARNING: dagster-webserver webapp not found and js_modules/ directory "
                "is not available. The webserver will start without the UI. "
                "To fix this, either:\n"
                "  - Install from PyPI: pip install dagster-webserver\n"
                "  - Build the UI manually: see build_js.sh in the repo root",
                file=sys.stderr,
            )
            return

        if not shutil.which("node"):
            print(
                "WARNING: Node.js not found. Cannot build dagster-webserver webapp. "
                "Install Node.js >= 20 and try again, or install from PyPI.",
                file=sys.stderr,
            )
            return

        self._build_webapp(js_modules, webapp_build)

    def _find_js_modules(self) -> str | None:
        """Walk up from package root to find js_modules/."""
        # Standard layout: <repo>/python_modules/dagster-webserver/ -> <repo>/js_modules/
        candidate = os.path.normpath(os.path.join(self.root, "..", "..", "js_modules"))
        if os.path.isdir(candidate):
            return candidate

        # dagster-oss subfolder layout
        candidate_oss = os.path.normpath(
            os.path.join(self.root, "..", "..", "dagster-oss", "js_modules")
        )
        if os.path.isdir(candidate_oss):
            return candidate_oss

        return None

    def _build_webapp(self, js_modules: str, webapp_build: str) -> None:
        """Run the JS build chain and copy output to webapp/build/."""
        print("Building dagster-webserver webapp from source...")

        app_oss = os.path.join(js_modules, "app-oss")
        webserver_pkg = os.path.join(self.root, "dagster_webserver")
        env = {**os.environ, "COREPACK_ENABLE_DOWNLOAD_PROMPT": "0"}

        try:
            # Enable corepack for Yarn
            subprocess.run(["corepack", "enable"], check=True, cwd=js_modules, env=env)

            # Install JS dependencies
            subprocess.run(["yarn", "install"], check=True, cwd=js_modules, env=env)

            # Build Next.js app
            subprocess.run(
                ["npx", "next", "build"], check=True, cwd=app_oss, env=env
            )

            # Replace asset prefix placeholders
            subprocess.run(
                ["node", os.path.join(app_oss, "replace-asset-prefix.js")],
                check=True,
                cwd=app_oss,
                env=env,
            )

            # Copy build output to webserver package (mirrors app-oss/build.sh)
            webapp_dir = os.path.join(webserver_pkg, "webapp")
            if os.path.exists(webapp_dir):
                shutil.rmtree(webapp_dir)
            os.makedirs(webapp_dir, exist_ok=True)

            shutil.copytree(
                os.path.join(app_oss, "build"),
                os.path.join(webapp_dir, "build"),
            )

            # Copy GraphiQL vendor files
            vendor_dir = os.path.join(webapp_dir, "build", "vendor")
            os.makedirs(vendor_dir, exist_ok=True)
            shutil.copytree(
                os.path.join(webserver_pkg, "graphiql"),
                os.path.join(vendor_dir, "graphiql"),
            )

            # Copy CSP header
            shutil.copy2(
                os.path.join(app_oss, "csp-header.txt"),
                os.path.join(webapp_dir, "build", "csp-header.txt"),
            )

            print("dagster-webserver webapp built successfully.")

        except FileNotFoundError as e:
            print(
                f"WARNING: Failed to build webapp - missing tool: {e}. "
                "Install Node.js >= 20 with corepack support.",
                file=sys.stderr,
            )
        except subprocess.CalledProcessError as e:
            print(
                f"WARNING: Failed to build webapp - command failed: {e}. "
                "The webserver will start without the UI.",
                file=sys.stderr,
            )
