## @dagster-io/eslint-config

Shared eslint configuration to be used in Dagster apps.

## Usage

### 1. Install

```bash
yarn -D add @dagster-io/eslint-config
```

### 2. Add to your project's eslint configuration

```js
// .eslintrc.js
module.exports = {
  extends: ['@dagster-io/eslint-config'],
};
```

If you are extending other configurations, put those first.

```js
// .eslintrc.js
module.exports = {
  extends: ['some-other-config', '@dagster-io/eslint-config'],
};
```

You can add other rules and settings to your `.eslintrc` as needed.
