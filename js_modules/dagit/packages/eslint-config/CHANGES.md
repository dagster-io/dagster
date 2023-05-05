## 1.0.11 (March 31, 2023)

- Dependency upgrades: Jest 29, TypeScript 5+, `@typescript-eslint` packages.
- Update `missing-graphql-variables-type` to fix mutations and subscriptions as well.

## 1.0.10 (Janaury 11, 2022)

- Restore `missing-graphql-variables-type`. The new codegen approach had too many drawbacks for developer experience.

## 1.0.9 (January 11, 2022)

- Add `ignoreExternal` on `import/no-cycle` rule to repair lint times

## 1.0.8 (January 6, 2022)

- Remove `missing-graphql-variables-type`, which is no longer needed now that we're using `graphql-codegen` instead of Apollo codegen.

## 1.0.7 (December 22, 2022)

- Disallow `moment`
- Bump dependencies

## 1.0.6 (November 16, 2022)

## 1.0.5 (June 2, 2022)

- Add rule to require GraphQL query variables

## 1.0.4 (May 16, 2022)

- Add recommended Jest lint configuration

## 1.0.3 (May 2, 2022)

- Bump dependencies

## 1.0.2 (April 13, 2022)

- Enable `object-shorthand`
- Add lint and prettier to this package

## 1.0.1 (April 7, 2022)

- Fix dependencies

## 1.0.0 (April 6, 2022)

- Initial commit
