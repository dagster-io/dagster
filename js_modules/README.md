## Dagster UI

The Dagster frontend application is built with TypeScript and React.

This directory contains the following packages:

- `app-oss`: A thin Next.js wrapper that serves as the root of the app.
- `ui-core`: The main components and routes of the application.
- `ui-components`: The core React component library, representing our design system
- `eslint-config`: A custom eslint configuration used across our frontend projects.

### Workspace configuration

Internally, the sub-packages (`packages/*`) are registered as workspaces in the repository root `package.json`, so there is no `package.json` or `.yarnrc.yml` at this directory level. Instead, the OSS versions of these files are stored under alternative names that Yarn ignores:

- `package.oss.json` — the workspace-root `package.json` used by the OSS repo
- `.yarnrc.oss.yml` — the Yarn configuration used by the OSS repo
- `yarn.oss.lock` - The Yarn lockfile used by the oSS repo

Copybara renames these files back to their standard names when syncing to the public `dagster-io/dagster` repository, and reverses the rename when syncing changes back in.

In OSS, the package.json and Yarn can therefore behave as if `dagster-ui` is itself the workspace. The dagster-ui `yarn.lock` will be updated after Copybara renames the files, in order to pick up any changes to dependencies within `dagster-ui`. This updated `yarn.lock` will then be synced back to internal, and developers working on `internal` should not have to commit any changes for it.

### Contributing

There are a handful of commands you can run locally from the `dagster-ui` directory prior to pushing a branch for a pull request:

- `make ts`: Run TypeScript checks across all packages.
- `make lint`: Run eslint (including prettier and autofixes) across all packages.
- `make jest`: Run Jest tests across all packages.

Each `make` command runs the named command within each package directory. For instance, `make ts` will run `yarn ts` in each of the package directories.

If you are making changes to GraphQL queries or fragments, you will also need to run `make generate-graphl`. This step builds new TypeScript types for queries and fragments. After regenerating GraphQL types, run `make ts` and `make lint` to find locations in the code where the updated types have resulted type and lint errors, and fix the errors prior to pushing the change.
