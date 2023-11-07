module.exports = {
  parser: '@typescript-eslint/parser',
  extends: [
    'plugin:eslint-plugin-dagster-rules/all',
    'plugin:react/recommended',
    'plugin:jest/recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:prettier/recommended', // Prettier plugin must be last!
  ],
  plugins: ['react-hooks', 'import'],
  parserOptions: {
    ecmaVersion: 2018,
    // Allows for the parsing of modern ECMAScript features
    sourceType: 'module',
    // Allows for the use of imports
    ecmaFeatures: {
      jsx: true, // Allows for the parsing of JSX
    },
  },
  rules: {
    curly: 'error',
    eqeqeq: [
      'error',
      'always',
      {
        null: 'ignore',
      },
    ],
    'import/no-cycle': ['error', {ignoreExternal: true}],
    'import/no-default-export': 'error',
    'import/no-duplicates': 'error',
    'import/order': [
      'error',
      {
        alphabetize: {
          order: 'asc',
          caseInsensitive: false,
        },
        'newlines-between': 'always',
      },
    ],
    'no-alert': 'error',
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
      },
    ],
    'object-shorthand': ['error', 'always'],
    'react/jsx-curly-brace-presence': 'error',
    'react/jsx-no-target-blank': 'error',
    'react/prefer-stateless-function': 'error',
    'react/prop-types': 'off',
    'react/display-name': 'off',
    '@typescript-eslint/ban-types': [
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
    '@typescript-eslint/no-unused-vars': [
      'error',
      {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
        ignoreRestSiblings: true,
      },
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
    react: {
      version: 'detect', // Tells eslint-plugin-react to automatically detect the version of React to use
    },
  },
};
