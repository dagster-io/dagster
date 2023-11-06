exports.settings = {
  bullet: '-',
  emphasis: '_',
  strong: '*',
  listItemIndent: 'one',
  rule: '-',
  // https://github.com/remarkjs/remark/tree/main/packages/remark-stringify#options
};
exports.plugins = [
  require('remark-frontmatter'),
  // GitHub Flavored Markdown's table pipe alignment
  [require('remark-gfm'), {tablePipeAlign: true}],
];
