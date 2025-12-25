# @dagster-io/eslint-config

Shared ESLint configuration for Dagster applications.

**Version 2.x+** requires **ESLint 9** and uses the flat config format.

For ESLint 8 support, use version 1.x.

## Installation

```bash
yarn add -D @dagster-io/eslint-config eslint@^9.0.0 prettier@^3.3.3
```

## Usage

### ESLint 9 Flat Config (eslint.config.js)

Create an `eslint.config.js` file in your project root:

```javascript
const dagsterConfig = require('@dagster-io/eslint-config');

module.exports = [
  ...dagsterConfig,
  // Your custom overrides here
  {
    rules: {
      // Override specific rules
    },
  },
];
```

### With Ignores

```javascript
const dagsterConfig = require('@dagster-io/eslint-config');

module.exports = [
  ...dagsterConfig,
  {
    ignores: ['dist/**', 'build/**', '*.config.js'],
  },
];
```

### With Additional Plugins

```javascript
const dagsterConfig = require('@dagster-io/eslint-config');
const storybookPlugin = require('eslint-plugin-storybook');

module.exports = [
  ...dagsterConfig,
  ...storybookPlugin.configs['flat/recommended'],
  {
    // Additional configuration
  },
];
```

## Migration from v1 to v2

### Step 1: Upgrade Dependencies

```bash
yarn add -D eslint@^9.0.0 @dagster-io/eslint-config@^2.0.0
```

### Step 2: Rename Config File

Rename `.eslintrc.js` → `eslint.config.js`

### Step 3: Update Config Format

**Before (.eslintrc.js):**

```javascript
module.exports = {
  extends: ['@dagster-io/eslint-config'],
  ignorePatterns: ['dist/**'],
  overrides: [
    {
      files: ['*.test.ts'],
      rules: {
        '@typescript-eslint/no-explicit-any': 'off',
      },
    },
  ],
};
```

**After (eslint.config.js):**

```javascript
const dagsterConfig = require('@dagster-io/eslint-config');

module.exports = [
  ...dagsterConfig,
  {
    ignores: ['dist/**'],
  },
  {
    files: ['*.test.ts'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },
];
```

### Step 4: Update Scripts (if needed)

ESLint 9 with flat config auto-detects files and config location.

**Before:**

```json
{
  "scripts": {
    "lint": "eslint . --ext .ts,.tsx -c .eslintrc.js"
  }
}
```

**After:**

```json
{
  "scripts": {
    "lint": "eslint ."
  }
}
```

### Key Differences in Flat Config

1. **Config is an array** - Multiple config objects can be specified
2. **No `extends`** - Configs are imported and spread: `...dagsterConfig`
3. **Ignores replace ignorePatterns** - Use `ignores: ['pattern']` in config objects
4. **Overrides are separate objects** - Each override is its own config object in the array
5. **File patterns in `files` key** - Override specific files with `files: ['*.test.ts']`

## Custom Rules

This config includes custom Dagster-specific ESLint rules:

### `dagster-rules/missing-graphql-variables-type`

Ensures GraphQL queries and mutations specify the Variables type parameter.

**❌ Incorrect:**

```typescript
const {data} = useQuery<SomeQuery>(SOME_QUERY);
```

**✅ Correct:**

```typescript
const {data} = useQuery<SomeQuery, SomeQueryVariables>(SOME_QUERY);
```

### `dagster-rules/no-oss-imports`

Prevents relative imports of `.oss` files and enforces absolute path imports.

**❌ Incorrect:**

```typescript
import {Component} from './Component.oss';
```

**✅ Correct:**

```typescript
import {Component} from 'shared/components/Component.oss';
```

### `dagster-rules/no-apollo-client`

Enforces using Dagster's wrapped Apollo client with performance instrumentation.

**❌ Incorrect:**

```typescript
import {useQuery} from '@apollo/client';
```

**✅ Correct:**

```typescript
import {useQuery} from '../apollo-client';
// or
import {useQuery} from '@dagster-io/ui-core/apollo-client';
```

### `dagster-rules/no-react-router-route`

Enforces using Dagster's custom `Route` component instead of react-router-dom's.

**❌ Incorrect:**

```typescript
import {Route} from 'react-router-dom';
```

**✅ Correct:**

```typescript
import {Route} from '../app/Route';
// or
import {Route} from '@dagster-io/ui-core/app/Route';
```

### `dagster-rules/missing-shared-import`

Validates that imports using the `shared/` path reference files ending with `.oss`.

## Included Rules and Plugins

This config includes:

- **TypeScript** - `@typescript-eslint` recommended rules
- **React** - React recommended rules + JSX runtime
- **Jest** - Jest recommended rules
- **Prettier** - Prettier integration with auto-formatting
- **Import** - Import ordering and cycle detection
- **React Hooks** - Rules of Hooks and exhaustive deps
- **Unused Imports** - Auto-removal of unused imports
- **Custom Dagster Rules** - Dagster-specific linting rules

## Rule Highlights

- **Import Ordering** - Automatically sorts imports by type and alphabetically
- **No Default Exports** - Enforces named exports for better refactoring
- **No Unused Imports** - Automatically removes unused imports
- **Restricted Imports** - Prevents use of deprecated libraries (moment, lodash, etc.)
- **React Best Practices** - Enforces modern React patterns
- **TypeScript Strictness** - Disallows non-null assertions and other unsafe patterns

## Compatibility

- **ESLint**: ^9.0.0
- **Node.js**: 18.18+, 20.9+, 21+
- **TypeScript**: Any version (via typescript-eslint v8)

## Legacy Version (ESLint 8)

If you need ESLint 8 support, install version 1.x:

```bash
yarn add -D @dagster-io/eslint-config@^1.0.0 eslint@^8.57.1
```

Then use the legacy `.eslintrc.js` format:

```javascript
// .eslintrc.js
module.exports = {
  extends: ['@dagster-io/eslint-config'],
};
```

## Contributing

This package is part of the Dagster monorepo. To make changes:

1. Update the config in `/js_modules/dagster-ui/packages/eslint-config`
2. Test locally with `yarn lint` and `yarn test`
3. Update version in `package.json`
4. Update `CHANGELOG.md` with changes
5. Submit a PR

## License

Apache-2.0
