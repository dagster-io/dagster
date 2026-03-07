import dagsterConfig from '@dagster-io/eslint-config';

// eslint-disable-next-line import/no-default-export
export default [
  ...dagsterConfig,
  {
    ignores: ['next-env.d.ts'],
  },
];
