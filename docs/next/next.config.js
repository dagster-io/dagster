const ExtraWatchPlugin = require('extra-watch-webpack-plugin');
const path = require('path');
const visit = require('unist-util-visit');
const fs = require('fs');
const limitSnippetLines = require('./src/scripts/limitSnippetLines');

const DIRECTIVE_PATTERN = 'literalinclude';

const transform = () => (tree) => {
  const visitor = (node) => {
    const { value, meta } = node;
    const metaValues = meta ? meta.split(' ') : [];
    if (metaValues.includes(DIRECTIVE_PATTERN)) {
      const data = value.trim();
      const values = data.split('\n').map((i) => i.trim().split(':'));
      const map = {};
      for (const val of values) {
        map[val[0]] = val[1];
      }

      const REPO = process.env.DAGSTER_REPO || path.join(__dirname, '../../');

      // TODO: Remove this (I think it's not needed anymore since we're defaultin to dirname)
      if (!REPO) {
        node.value =
          'Unable to produce literal include: Environment variable $DAGSTER_REPO is not set';
        return;
      }

      const isRelativeToProject =
        Object.keys(map).indexOf('relativeToProject') !== -1;

      const root = isRelativeToProject
        ? __dirname
        : path.join(REPO, '/examples/');

      const filePath = path.join(root, map.file);
      try {
        // TODO: Fix all other literal includes because now they need to include /dagster_examples/ in their paths
        const content = fs.readFileSync(filePath).toString();
        node.value = limitSnippetLines(content, map.lines);
      } catch (error) {
        node.value = `Unable to read file at: ${filePath}`;
      }
    }
  };

  visit(tree, 'code', visitor);
};

const withMDX = require('@next/mdx')({
  extension: /\.mdx?$/,
  options: {
    remarkPlugins: [transform],
  },
});

module.exports = withMDX({
  pageExtensions: ['mdx', 'jsx', 'js', 'ts', 'tsx'],
  assetPrefix: process.env.BASE_PATH || '',
  publicRuntimeConfig: {
    basePath: process.env.BASE_PATH || '',
    version:
      process.env.VERSION ||
      (process.env.BASE_PATH && process.env.BASE_PATH.substr(1)) ||
      '',
  },
  webpack: (config) => {
    config.plugins.push(
      new ExtraWatchPlugin({
        dirs: [path.join(config.context, 'pages')],
      }),
    );
    return config;
  },
});
