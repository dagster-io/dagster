module.exports = {
  stories: ['../src/**/*.stories.mdx', '../src/**/*.stories.@(js|jsx|ts|tsx)'],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
  ],
  // https://storybook.js.org/docs/react/configure/webpack#bundle-splitting
  features: {
    storyStoreV7: true,
  },
  // https://github.com/storybookjs/storybook/issues/16690#issuecomment-971579785
  webpackFinal: async (config) => {
    config.module.rules.push({
      test: /\.mjs$/,
      include: /node_modules/,
      type: "javascript/auto",
    })
    return config
  },
};
