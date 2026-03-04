import dagsterConfig from '@dagster-io/eslint-config';
import storybookPlugin from 'eslint-plugin-storybook';
import graphqlPlugin from '@graphql-eslint/eslint-plugin';

// eslint-disable-next-line import/no-default-export
export default [
  ...dagsterConfig,
  ...storybookPlugin.configs['flat/recommended'],
  {
    files: ['src/**/*.ts', 'src/**/*.tsx'],
    processor: graphqlPlugin.processor,
    languageOptions: {
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
  },
  {
    files: ['**/*.graphql'],
    plugins: {
      '@graphql-eslint': graphqlPlugin,
    },
    languageOptions: {
      parser: graphqlPlugin.parser,
      parserOptions: {
        graphQLConfig: {
          schema: './src/graphql/schema.graphql',
          documents: ['src/**/*.{ts,tsx}', '!src/graphql/**', '!src/**/types/*.types.ts'],
        },
      },
    },
    rules: {
      ...graphqlPlugin.configs['flat/operations-recommended'].rules,
      '@graphql-eslint/naming-convention': 'off',
      '@graphql-eslint/no-unused-fragments': 'off',
      '@graphql-eslint/selection-set-depth': 'off',
    },
  },
  {
    ignores: ['src/graphql/**', 'src/**/types/*.types.ts', 'src/**/generated/**'],
  },
];
