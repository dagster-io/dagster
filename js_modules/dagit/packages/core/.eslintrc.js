const fs = require('fs');
const path = require('path');

const schemaPath = path.resolve(path.join(__dirname, 'src', 'graphql', 'schema.graphql'));
const schema = fs.readFileSync(schemaPath).toString();

module.exports = {
  extends: [
    'plugin:storybook/recommended', '@dagster-io/eslint-config',
  ],
  plugins: ['graphql'],
  rules: {
    'graphql/required-fields': [
      'error',
      {
        env: 'apollo',
        schemaString: schema,
        requiredFields: ['id'],
      },
    ],
  },
};
