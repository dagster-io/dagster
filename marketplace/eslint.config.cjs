const tseslint = require('typescript-eslint');
const eslintPluginPrettierRecommended = require('eslint-plugin-prettier/recommended');

module.exports = [
  ...tseslint.configs.recommended,
  eslintPluginPrettierRecommended,
];
