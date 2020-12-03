#!/bin/bash
set -euo pipefail

# arc
mkdir ~/arc
cd ~/arc
git clone https://github.com/phacility/libphutil.git
git clone https://github.com/phacility/arcanist.git
git clone https://github.com/pinterest/arcanist-linters pinterest-linters

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

pyenv install 3.7.4
