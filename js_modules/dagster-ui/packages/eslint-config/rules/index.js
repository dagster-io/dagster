/* eslint-disable */
const projectName = 'dagster-rules';

const rules = {
  'missing-graphql-variables-type': require('./missing-graphql-variables-type').rule,
  'no-oss-imports': require('./no-oss-imports'),
  'no-apollo-client': require('./no-apollo-client'),
};

module.exports = {
  parser: `@typescript-eslint/parser`,
  configs: {
    all: {
      plugins: [projectName],
      rules: {
        [`${projectName}/missing-graphql-variables-type`]: 'error',
        [`${projectName}/no-oss-imports`]: 'error',
        [`${projectName}/no-apollo-client`]: 'error',
      },
    },
  },
  rules,
};
