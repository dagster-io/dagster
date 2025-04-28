module.exports = {
  parser: '@babel/eslint-parser',
  extends: [
    'plugin:react/recommended',
    'plugin:@docusaurus/recommended',
    'plugin:mdx/recommended',
    'plugin:prettier/recommended',
  ],
  rules: {
    'import/no-default-export': 'off',
    'react/react-in-jsx-scope': 'off',
  },
  ignorePatterns: ['build'],
  parserOptions: {
    extensions: ['.md', '.mdx'], // Resolve .md files as .mdx
    markdownExtensions: ['.md', '.markdown'], // Treat .md and .markdown files as plain markdown
  },
  overrides: [
    {
      files: ['*.md', '*.mdx'],
      extends: 'plugin:mdx/recommended',
      rules: {
        'react/jsx-no-undef': 'off',
        'react/no-unescaped-entities': 'off',
      },
    },
  ],
  settings: {
    react: {
      version: 'detect',
    },
  },
};
