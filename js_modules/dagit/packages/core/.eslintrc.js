module.exports = {
  extends: ['plugin:storybook/recommended', '@dagster-io/eslint-config'],
  ignorePatterns: ['src/graphql/**', 'src/**/types/*.types.ts'],
  plugins: ['graphql'],
  rules: {
    'graphql/required-fields': [
      'error',
      {
        env: 'apollo',
        requiredFields: ['id'],
      },
    ],
  },
};
