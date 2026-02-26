#!/bin/bash
set -eux

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEBSERVER_DIR="$SCRIPT_DIR/../../python_modules/dagster-webserver/dagster_webserver"

# Build Next.js app
npx next build

# Replace asset prefix placeholders
node "$SCRIPT_DIR/replace-asset-prefix.js"

# Copy build output to webserver package
rm -rf "$WEBSERVER_DIR/webapp"
mkdir -p "$WEBSERVER_DIR/webapp"
cp -r "$SCRIPT_DIR/build" "$WEBSERVER_DIR/webapp/"
mkdir -p "$WEBSERVER_DIR/webapp/build/vendor"
cp -r "$WEBSERVER_DIR/graphiql" "$WEBSERVER_DIR/webapp/build/vendor"
cp "$SCRIPT_DIR/csp-header.txt" "$WEBSERVER_DIR/webapp/build"
