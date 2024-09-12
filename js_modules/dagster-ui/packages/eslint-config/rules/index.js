/* eslint-disable */
const projectName = 'dagster-rules';

const rules = {
  'missing-graphql-variables-type': require('./missing-graphql-variables-type'),
  'no-oss-imports': require('./no-oss-imports'),
  'no-apollo-client': require('./no-apollo-client'),
  'no-react-router-route': require('./no-react-router-route'),
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
        [`${projectName}/no-react-router-route`]: 'error',
      },
    },
  },
  rules,
};
