module.exports = {
  bracketSpacing: false,
  bracketSameLine: true,
  singleQuote: true,
  trailingComma: 'all',
  printWidth: 120,
  overrides: [
    {
      files: ['docs/**/*.md', 'docs/**/*.mdx'],
      options: {
        parser: 'mdx',
        proseWrap: 'preserve',
        htmlWhitespaceSensitivity: 'ignore',
      },
    },
  ],
};
