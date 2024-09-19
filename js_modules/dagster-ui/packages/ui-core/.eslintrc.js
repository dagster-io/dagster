module.exports = {
  extends: ['plugin:storybook/recommended', '@dagster-io/eslint-config'],
  ignorePatterns: ['src/graphql/**', 'src/**/types/*.types.ts'],
  overrides: [
    {
      files: ['*.tsx', '*.ts'],
      processor: '@graphql-eslint/graphql',
    },
    {
      files: ['*.graphql'],
      extends: 'plugin:@graphql-eslint/schema-recommended',
      rules: {
        '@graphql-eslint/require-id-when-available': ['error', {fieldName: 'id'}],
      },
    },
  ],
};
