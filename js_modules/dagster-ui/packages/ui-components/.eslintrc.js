module.exports = {
  extends: ['plugin:storybook/recommended', '@dagster-io/eslint-config'],
  rules: {
    'dagster-rules/missing-graphql-variables-type': 'off',
  },
};
