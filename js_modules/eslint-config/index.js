const prettierConfig = require('eslint-config-prettier');
const dagsterRulesPlugin = require('eslint-plugin-dagster-rules');
const importPlugin = require('eslint-plugin-import');
const jestPlugin = require('eslint-plugin-jest');
const jsxA11yPlugin = require('eslint-plugin-jsx-a11y');
const prettierPlugin = require('eslint-plugin-prettier');
const reactPlugin = require('eslint-plugin-react');
const reactHooksPlugin = require('eslint-plugin-react-hooks');
const unusedImportsPlugin = require('eslint-plugin-unused-imports');
const tseslint = require('typescript-eslint');

module.exports = [
  // TypeScript recommended config
  ...tseslint.configs.recommended,

  // React recommended config (using flat config preset)
  reactPlugin.configs.flat.recommended,

  // React JSX runtime (for React 17+)
  reactPlugin.configs.flat['jsx-runtime'],

  // Jest recommended config (using flat config preset)
  jestPlugin.configs['flat/recommended'],

  // Main configuration object
  {
    plugins: {
      '@typescript-eslint': tseslint.plugin,
      react: reactPlugin,
      'react-hooks': reactHooksPlugin,
      jest: jestPlugin,
      import: importPlugin,
      'unused-imports': unusedImportsPlugin,
      'jsx-a11y': jsxA11yPlugin,
      'dagster-rules': dagsterRulesPlugin,
    },

    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        ecmaVersion: 2018,
        sourceType: 'module',
        ecmaFeatures: {
          jsx: true,
        },
      },
    },

    settings: {
      react: {
        version: 'detect',
      },
    },

    rules: {
      // Custom Dagster rules
      'dagster-rules/missing-graphql-variables-type': 'error',
      'dagster-rules/no-oss-imports': 'error',
      'dagster-rules/no-apollo-client': 'error',
      'dagster-rules/no-react-router-route': 'error',
      'dagster-rules/missing-shared-import': 'error',

      // General rules
      curly: 'error',
      eqeqeq: ['error', 'always', {null: 'ignore'}],

      // Import rules
      'import/no-cycle': ['error', {ignoreExternal: true}],
      'import/no-default-export': 'error',
      'import/no-duplicates': 'error',
      'import/order': [
        'error',
        {
          groups: ['builtin', 'external', 'internal', ['sibling', 'parent'], 'index', 'unknown'],
          alphabetize: {
            order: 'asc',
            caseInsensitive: false,
          },
          'newlines-between': 'always',
        },
      ],

      'sort-imports': [
        'error',
        {
          ignoreCase: false,
          ignoreDeclarationSort: true,
          ignoreMemberSort: false,
          allowSeparatedGroups: true,
        },
      ],

      'no-alert': 'error',
      'no-restricted-properties': [
        'error',
        {
          object: 'window',
          property: 'open',
          message: 'Please use the `useOpenInNewTab` hook instead.',
        },
      ],
      'no-restricted-globals': [
        'error',
        {
          name: 'open',
          message: 'Please use the `useOpenInNewTab` hook instead.',
        },
      ],

      // Unused imports rules
      'no-unused-vars': 'off',
      'unused-imports/no-unused-imports': 'error',
      'unused-imports/no-unused-vars': [
        'error',
        {
          vars: 'all',
          varsIgnorePattern: '^_',
          args: 'after-used',
          argsIgnorePattern: '^_',
        },
      ],

      'no-restricted-imports': [
        'error',
        {
          paths: [
            {
              name: '@blueprintjs/core',
              message: 'Please use components from @dagster-io/ui-components instead.',
            },
            {
              name: '@blueprintjs/popover2',
              message: 'Please use components from @dagster-io/ui-components instead.',
            },
            {
              name: '@blueprintjs/select',
              message: 'Please use components from @dagster-io/ui-components instead.',
            },
            {
              name: 'graphql-tag',
              message: 'Please import from `@apollo/client`.',
            },
            {
              name: 'graphql.macro',
              importNames: ['gql'],
              message: 'Please import from `@apollo/client`.',
            },
            {
              name: 'lodash',
              message: 'Please import specific lodash modules, e.g. `lodash/throttle`.',
            },
            {
              name: 'moment',
              message: 'Please use native Intl APIs for date/time, or dayjs if necessary.',
            },
            {
              name: 'moment-timezone',
              message: 'Please use native Intl APIs for date/time, or dayjs if necessary.',
            },
          ],
          patterns: [
            {
              group: ['dayjs/plugin/*'],
              message: 'Please load and configure dayjs plugins in dayjsExtensions.ts',
            },
          ],
        },
      ],

      'object-shorthand': ['error', 'always'],

      // React rules
      'react/jsx-curly-brace-presence': 'error',
      'react/jsx-no-target-blank': 'error',
      'react/jsx-uses-react': 'off',
      'react/prefer-stateless-function': 'error',
      'react/prop-types': 'off',
      'react/display-name': 'off',
      'react/react-in-jsx-scope': 'off',

      // TypeScript rules
      '@typescript-eslint/no-restricted-types': [
        'error',
        {
          types: {
            'React.FC':
              'Useless and has some drawbacks, see https://github.com/facebook/create-react-app/pull/8177',
            'React.FunctionComponent':
              'Useless and has some drawbacks, see https://github.com/facebook/create-react-app/pull/8177',
            'React.FunctionalComponent':
              'Preact specific, useless and has some drawbacks, see https://github.com/facebook/create-react-app/pull/8177',
          },
        },
      ],
      '@typescript-eslint/no-unused-vars': 'off',
      '@typescript-eslint/interface-name-prefix': 'off',
      '@typescript-eslint/explicit-function-return-type': 'off',
      '@typescript-eslint/explicit-member-accessibility': 'off',
      '@typescript-eslint/explicit-module-boundary-types': 'off',
      '@typescript-eslint/camelcase': 'off',
      '@typescript-eslint/no-empty-function': 'off',
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/array-type': 'off',
      '@typescript-eslint/no-use-before-define': 'off',
      '@typescript-eslint/no-non-null-assertion': 'error',
      '@typescript-eslint/prefer-interface': 'off',
      '@typescript-eslint/no-empty-interface': 'off',
      '@typescript-eslint/no-empty-object-type': [
        'error',
        {allowInterfaces: 'with-single-extends'},
      ],

      // React Hooks rules
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'error',
    },
  },

  // Prettier config MUST be last to override formatting rules
  prettierConfig,
  {
    plugins: {
      prettier: prettierPlugin,
    },
    rules: {
      'prettier/prettier': 'error',
      curly: 'error',
    },
  },
];
