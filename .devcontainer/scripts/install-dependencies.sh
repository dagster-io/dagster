#!/bin/bash
set -euo pipefail

function fyi {
  local content=$1

  local CGREEN="$(tput setaf 2)👋  "
  local CRESET="$(tput sgr0)"

  echo "${CGREEN} ${content}${CRESET}"
}

# arc
mkdir ~/arc
cd ~/arc
git clone https://github.com/phacility/libphutil.git
git clone https://github.com/phacility/arcanist.git
git clone https://github.com/pinterest/arcanist-linters pinterest-linters

export PATH="$HOME/arc/arcanist/bin/:$PATH"
{
  echo ''
  echo 'export PATH="$HOME/arc/arcanist/bin/:$PATH"'
} >> ~/.bashrc

# pyenv
curl https://pyenv.run | bash

export PATH="$HOME/.pyenv/bin:$PATH"

{
  echo ''
  echo 'export PATH="$HOME/.pyenv/bin:$PATH"'
  echo 'eval "$(pyenv init -)"'
  echo 'eval "$(pyenv virtualenv-init -)"'
} >> ~/.bashrc

cd ~/workspace/dagster
pyenv install 3.7.4
pyenv virtualenv 3.7.4 dagster-3.7.4

fyi "Please run \`exec \$SHELL\` to reload the current shell!"
