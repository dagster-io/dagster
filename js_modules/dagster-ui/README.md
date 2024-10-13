## Dagster UI

The Dagster frontend application is built with TypeScript and React.

This directory contains the following packages:

- `app-oss`: A thin Next.js wrapper that serves as the root of the app.
- `ui-core`: The main components and routes of the application.
- `ui-components`: The core React component library, representing our design system
- `eslint-config`: A custom eslint configuration used across our frontend projects.

### Contributing

There are a handful of commands you can run locally from the `dagster-ui` directory prior to pushing a branch for a pull request:

- `make ts`: Run TypeScript checks across all packages.
- `make lint`: Run eslint (including prettier and autofixes) across all packages.
- `make jest`: Run Jest tests across all packages.

Each `make` command runs the named command within each package directory. For instance, `make ts` will run `yarn ts` in each of the package directories.

If you are making changes to GraphQL queries or fragments, you will also need to run `make generate-graphl`. This step builds new TypeScript types for queries and fragments. After regenerating GraphQL types, run `make ts` and `make lint` to find locations in the code where the updated types have resulted type and lint errors, and fix the errors prior to pushing the change.
