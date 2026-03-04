const projectName = 'dagster-rules';
const packageJson = require('../package.json');

const rules = {
  'missing-graphql-variables-type': require('./missing-graphql-variables-type'),
  'no-oss-imports': require('./no-oss-imports'),
  'no-apollo-client': require('./no-apollo-client'),
  'no-react-router-route': require('./no-react-router-route'),
  'missing-shared-import': require('./missing-shared-import'),
};

module.exports = {
  meta: {
    name: 'eslint-plugin-dagster-rules',
    version: packageJson.version,
  },
  parser: `@typescript-eslint/parser`,
  configs: {
    all: {
      plugins: [projectName],
      rules: {
        [`${projectName}/missing-graphql-variables-type`]: 'error',
        [`${projectName}/no-oss-imports`]: 'error',
        [`${projectName}/no-apollo-client`]: 'error',
        [`${projectName}/no-react-router-route`]: 'error',
        [`${projectName}/missing-shared-import`]: 'error',
      },
    },
  },
  rules,
};
