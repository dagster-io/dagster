#!/bin/bash

if [[ "$VERCEL_ENV" != "production" ]]; then
  echo "🛑 - Not production, cancel build."
  exit 0;
fi

git diff --quiet HEAD^ HEAD ./
any_dagster_ui_changes=$?

if [[ $any_dagster_ui_changes -eq 1 ]]; then
  echo "✅ - Changes found in @dagster-io/ui-components, proceed with build."
  exit 1;
else
  echo "🛑 - No changes to @dagster-io/ui-components, cancel build."
  exit 0;
fi
