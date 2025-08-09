{
  pkgs,
  mkShell,
  ...
}:
mkShell {
  packages = with pkgs; [
    zsh
    uv
    gnumake
    yarn
  ];
  shellHook = ''
    uv python install 3.10
    uv venv --python 3.10
    source ./.venv/bin/activate
  '';
}
