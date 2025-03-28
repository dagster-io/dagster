module.exports = {
  bracketSpacing: false,
  bracketSameLine: true,
  singleQuote: true,
  trailingComma: 'all',
  overrides: [
    {
      files: ['docs/**/*.md', 'docs/**/*.mdx'],
      options: {
        parser: 'mdx',
        proseWrap: 'preserve',
        htmlWhitespaceSensitivity: 'ignore',
        printWidth: 1000, // needed to prevent wrapping of CodeExamples
        singleAttributePerLine: false, // needed to prevent wrapping of CodeExamples
      },
    },
  ],
};
