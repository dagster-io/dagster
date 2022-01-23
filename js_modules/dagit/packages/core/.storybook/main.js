const path = require('path');

module.exports = {
  stories: [
    "../src/**/*.stories.mdx",
    "../src/**/*.stories.@(js|jsx|ts|tsx)"
  ],
  addons: [
    "@storybook/addon-links",
    "@storybook/addon-essentials"
  ],
  framework: "@storybook/react",
  core: {
    builder: "webpack5",
  },
  // https://storybook.js.org/docs/react/configure/webpack#bundle-splitting
  features: {
    storyStoreV7: true,
  },
  // https://github.com/storybookjs/storybook/issues/16690#issuecomment-971579785
  webpackFinal: async (config) => {
    // console.log(path.resolve('../ui/src'));
    // process.exit(1);
    return {
      ...config,
      resolve: {
        ...config.resolve,
        alias: {
          ...config.resolve.alias,
          '@dagster-io/ui': path.resolve('../ui/src'),
        },
      },
      module: {
        ...config.module,
        rules: [...config.module.rules, {
          test: /\.mjs$/,
          include: /node_modules/,
          type: "javascript/auto",
        }],
      },
    };
  },
}