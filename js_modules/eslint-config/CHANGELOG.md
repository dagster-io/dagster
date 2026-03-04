# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2025-12-22

### BREAKING CHANGES

- **Requires ESLint 9.0.0 or higher** - Dropped ESLint 8 support
- **Config format changed to ESLint flat config** - The package now exports a flat config array instead of a legacy .eslintrc object
- **Consumers must migrate to flat config** - Projects using this config must:
  - Upgrade to ESLint 9: `yarn add -D eslint@^9.0.0`
  - Rename `.eslintrc.js` to `eslint.config.js`
  - Update config format (see README.md for migration guide)

### Added

- Full ESLint 9 flat config support with modern plugin integration
- Plugin metadata (`meta.name` and `meta.version`) to custom `eslint-plugin-dagster-rules`
- Dependency on `typescript-eslint` package for simplified flat config usage
- Comprehensive migration guide in README.md

### Changed

- Main config (`index.js`) completely restructured to export flat config array
- All plugin references updated to use flat config formats where available
- Self-linting config converted from `.eslintrc.js` to `eslint.config.js`
- Package scripts updated to use ESLint 9 CLI (removed `--ext` and `-c` flags)
- Updated peer dependency: `eslint` from `^8.57.1` to `^9.0.0`
- Updated dev dependency: `eslint` from `^8.57.1` to `^9.0.0`

### Migration Guide

See README.md for detailed migration instructions from v1.x to v2.0.0.

**Quick Migration Steps:**

1. Upgrade ESLint: `yarn add -D eslint@^9.0.0`
2. Upgrade this package: `yarn add -D @dagster-io/eslint-config@^2.0.0`
3. Rename `.eslintrc.js` → `eslint.config.js`
4. Update config:

   ```javascript
   // Before (.eslintrc.js)
   module.exports = {
     extends: ['@dagster-io/eslint-config'],
   };

   // After (eslint.config.js)
   const dagsterConfig = require('@dagster-io/eslint-config');
   module.exports = [...dagsterConfig];
   ```

## [1.0.21] - Previous Release

See git history for changes prior to v2.0.0.
