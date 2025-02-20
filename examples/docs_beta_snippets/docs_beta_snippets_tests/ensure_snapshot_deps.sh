#!/bin/bash

# Validate that tree is installed, install it if not (for bk purposes)
(which tree > /dev/null && echo "tree command found") ||
(which brew > /dev/null && echo "tree command not found, installing using brew..." && brew install tree) ||
(echo "tree command not found, installing using apt-get..." && apt-get install tree)
