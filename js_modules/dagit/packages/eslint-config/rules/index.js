/* eslint-disable */
const projectName = 'dagster-rules';

/**
 * As we add custom rules to the config, specify them in the `rules` map below
 * and enable them in the config.
 */

const rules = {
  // 'my-rule-type': require('./my-rule-type).rule,
};

module.exports = {
  parser: `@typescript-eslint/parser`,
  configs: {
    all: {
      plugins: [projectName],
      rules: {
        // [`${projectName}/my-rule-type`]: 'error',
      },
    },
  },
  rules,
};
