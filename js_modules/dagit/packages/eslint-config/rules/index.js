/* eslint-disable */
const projectName = 'dagster-rules';

const rules = {
  'missing-graphql-variables-type': require('./missing-graphql-variables-type').rule,
};

module.exports = {
  parser: `@typescript-eslint/parser`,
  configs: {
    all: {
      plugins: [projectName],
      rules: {
        [`${projectName}/missing-graphql-variables-type`]: 'error',
      },
    },
  },
  rules,
};
