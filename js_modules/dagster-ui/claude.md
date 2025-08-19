# Shared Components

Files with the extension `.oss.tsx` are shared components. These are components which have a corresponding `.cloud.tsx` file that exist in our internal package `cd $DAGSTER_INTERNAL_GIT_REPO_DIR/dagster-cloud/js_modules/app-cloud`. In OSS we build the app using the `.oss.tsx` files. In cloud we build the app using `.cloud.tsx` files.

# Testing Dagster UI

The packages contained within are part of a yarn workspace.
Check the respective package.json for the available commands.

For example to run tests first cd to the appropriate package, eg:

```
cd $DAGSTER_GIT_REPO_DIR/js_modules/dagster-ui/packages/ui-core
```

Then run jest:

```
yarn jest
```
