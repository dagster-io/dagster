import dagsterConfig from '@dagster-io/eslint-config';
import storybookPlugin from 'eslint-plugin-storybook';

// eslint-disable-next-line import/no-default-export
export default [
  ...dagsterConfig,
  ...storybookPlugin.configs['flat/recommended'],
  {
    rules: {
      'dagster-rules/missing-graphql-variables-type': 'off',
    },
  },
];
