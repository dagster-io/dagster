const withMarkdoc = require('@markdoc/next.js');

module.exports = withMarkdoc({schemaPath: './markdoc', mode: 'static'})({
  pageExtensions: ['js', 'jsx', 'ts', 'tsx', 'md', 'mdoc'],
});
