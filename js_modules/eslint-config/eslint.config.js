const baseConfig = require('./index.js');

module.exports = [
  ...baseConfig,
  {
    rules: {
      '@typescript-eslint/no-require-imports': 'off',
      '@typescript-eslint/no-var-requires': 'off',
    },
  },
];
