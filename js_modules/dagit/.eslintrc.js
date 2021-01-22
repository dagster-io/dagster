const fs = require('fs');
const path = require('path');

const schemaPath = path.resolve(path.join(__dirname, 'src', 'graphql', 'schema.graphql'));
const schema = fs.readFileSync(schemaPath).toString();

module.exports = {
  parser: '@typescript-eslint/parser', // Specifies the ESLint parser
  extends: [
    'plugin:react/recommended',
    'plugin:@typescript-eslint/recommended', // Uses the recommended rules from the @typescript-eslint/eslint-plugin
    'prettier/@typescript-eslint', // Uses eslint-config-prettier to disable ESLint rules from @typescript-eslint/eslint-plugin that would conflict with prettier
    'plugin:prettier/recommended', // Enables eslint-plugin-prettier and displays prettier errors as ESLint errors. Make sure this is always the last configuration in the extends array.
  ],
  plugins: ['react-hooks', 'import', 'graphql'],
  parserOptions: {
    ecmaVersion: 2018, // Allows for the parsing of modern ECMAScript features
    sourceType: 'module', // Allows for the use of imports
    ecmaFeatures: {
      jsx: true, // Allows for the parsing of JSX
    },
  },
  rules: {
    curly: 'error',
    'graphql/required-fields': [
      'error',
      {
        env: 'apollo',
        schemaString: schema,
        requiredFields: ['id'],
      },
    ],
    'import/no-cycle': 'error',
    'import/no-default-export': 'error',
    'import/no-duplicates': 'error',
    'import/order': [
      'error',
      {
        alphabetize: {order: 'asc', caseInsensitive: false},
        'newlines-between': 'always',
      },
    ],
    'no-restricted-imports': [
      'error',
      {
        patterns: ['./*', '../*'],
        paths: [
          {
            name: '@blueprintjs/core',
            importNames: ['Alert', 'Callout', 'Spinner'],
            message: 'Please use components in src/ui instead.',
          },
        ],
      },
    ],
    'react/prefer-stateless-function': 'error',
    'react/prop-types': 'off',
    'react/display-name': 'off',
    '@typescript-eslint/no-unused-vars': [
      'error',
      {argsIgnorePattern: '^_', varsIgnorePattern: '^_', ignoreRestSiblings: true},
    ],
    '@typescript-eslint/interface-name-prefix': 'off',
    '@typescript-eslint/explicit-function-return-type': 'off',
    '@typescript-eslint/explicit-member-accessibility': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/camelcase': 'off',
    '@typescript-eslint/no-empty-function': 'off',
    '@typescript-eslint/no-explicit-any': 'off',
    '@typescript-eslint/no-empty-function': 'off',
    '@typescript-eslint/array-type': 'off',
    '@typescript-eslint/no-use-before-define': 'off',
    '@typescript-eslint/no-non-null-assertion': 'off',
    '@typescript-eslint/prefer-interface': 'off',
    '@typescript-eslint/no-empty-interface': 'off',
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
  },
  settings: {
    'import/internal-regex': '^src/',
    react: {
      version: 'detect', // Tells eslint-plugin-react to automatically detect the version of React to use
    },
  },
};
