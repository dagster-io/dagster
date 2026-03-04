import dagsterConfig from '@dagster-io/eslint-config';
import storybookPlugin from 'eslint-plugin-storybook';
import graphqlPlugin from '@graphql-eslint/eslint-plugin';

// Find the config object that contains the no-restricted-imports rule
const configWithNoRestrictedImports = dagsterConfig.find(
  (config) => config.rules?.['no-restricted-imports'],
);

// Extract the base rule configuration
const baseNoRestrictedImports = configWithNoRestrictedImports?.rules?.['no-restricted-imports'];
const [_severity, baseRuleConfig] = baseNoRestrictedImports || ['error', {}];

// eslint-disable-next-line import/no-default-export
export default [
  ...dagsterConfig,
  ...storybookPlugin.configs['flat/recommended'],
  {
    rules: {
      'no-restricted-imports': [
        'error',
        {
          paths: baseRuleConfig.paths || [],
          patterns: [
            ...(baseRuleConfig.patterns || []),
            {
              group: ['**/graphql/types-do-not-use'],
              message:
                'Import from graphql/types or graphql/builders, and use fragments instead of full type imports.',
            },
          ],
        },
      ],
    },
  },
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
