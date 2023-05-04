import path from 'path';

const config = {
  stories: ['../src/**/*.stories.mdx', '../src/**/*.stories.@(js|jsx|ts|tsx)'],
  addons: ['@storybook/addon-links', '@storybook/addon-essentials', '@storybook/addon-mdx-gfm'],
  framework: {
    name: '@storybook/react-webpack5',
    options: {},
  },
  // https://storybook.js.org/docs/react/configure/webpack#bundle-splitting
  features: {
    storyStoreV7: true,
  },
  // https://github.com/hipstersmoothie/react-docgen-typescript-plugin/issues/78#issuecomment-1409224863
  typescript: {
    reactDocgen: 'react-docgen-typescript-plugin',
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
        rules: [
          ...config.module.rules,
          {
            test: /\.mjs$/,
            include: /node_modules/,
            type: 'javascript/auto',
          },
        ],
      },
    };
  },
  docs: {
    autodocs: true,
  },
};

export default config;
