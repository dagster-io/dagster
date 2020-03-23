// const withSass = require("@zeit/next-sass");
// const tailwindCss = require("tailwindcss");
const ExtraWatchPlugin = require('extra-watch-webpack-plugin');
const path = require('path');
const emoji = require('remark-emoji');
const visit = require('unist-util-visit');
const fs = require('fs');

// TODO: Extract to it's own file
const transform = () => (tree) => {
  const visitor = (node) => {
    const { children } = node;
    if (
      children.length >= 1
      && children[0].value
      && children[0].value.includes('::literalinclude')
    ) {
      const { value } = children[0];
      const data = value.replace('::literalinclude', '').trim();
      const values = data
        .split(' ')
        .map((i) => i.substring(1, i.length - 1).split(':'));

      const map = {};
      for (const val of values) {
        map[val[0]] = val[1];
      }

      const { DAGSTER_REPO } = process.env;
      if (!DAGSTER_REPO) {
        node.type = 'code';
        node.children = undefined;
        node.lang = 'js';
        node.value = 'Unable to produce literal include: Environment variable $DAGSTER_REPO is not set';
        return;
      }

      const root = path.join(DAGSTER_REPO, '/examples/dagster_examples/');
      const filePath = path.join(root, map.file);
      const content = fs.readFileSync(filePath).toString();

      node.type = 'code';
      node.children = undefined;
      node.lang = 'js';
      node.value = content;
    }
  };
  visit(tree, 'paragraph', visitor);
};

const withMDX = require('@next/mdx')({
  extension: /\.mdx?$/,
  options: {
    remarkPlugins: [emoji, transform],
  },
});

module.exports = withMDX({
  pageExtensions: ['mdx', 'jsx', 'js', 'ts', 'tsx'],
  webpack: (config) => {
    config.plugins.push(
      new ExtraWatchPlugin({
        dirs: [path.join(config.context, 'pages')],
      }),
    );

    return config;
  },
});
