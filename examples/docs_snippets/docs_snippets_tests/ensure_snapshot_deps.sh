#!/bin/bash

# Validate that tree is installed, install it if not (for bk purposes)
(command -v tree > /dev/null && echo "tree command found") ||
(command -v brew > /dev/null && echo "tree command not found, installing using brew..." && brew install tree) ||
(echo "tree command not found, installing using apt-get..." && apt-get install tree)
