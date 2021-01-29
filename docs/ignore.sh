#!/bin/bash

if [[ "$VERCEL_ENV" == "production" ]] ; then
  # Proceed with the build
  exit 1;

else
  # Don't build
  exit 0;
fi
