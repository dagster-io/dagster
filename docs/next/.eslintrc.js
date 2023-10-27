module.exports = {
  extends: ['@dagster-io/eslint-config', 'plugin:@next/next/recommended'],
  rules: {
    'import/no-default-export': 'off',
    'react/react-in-jsx-scope': 'off',
  },
};
