exports.settings = {
  bullet: "-",
  emphasis: "_",
  strong: "*",
  listItemIndent: "one",
  rule: "-",
};
exports.plugins = [
  require("remark-frontmatter"),
  require("remark-preset-prettier"),
  // GitHub Flavored Markdown's table pipe alignment
  [require("remark-gfm"), { tablePipeAlign: true }],
];
