FROM mcr.microsoft.com/vscode/devcontainers/universal:linux

USER codespace

COPY scripts/install-dependencies.sh /tmp/
RUN bash /tmp/install-dependencies.sh
