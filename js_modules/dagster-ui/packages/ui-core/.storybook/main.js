import path, {dirname, join} from 'path';

/**
 * This function is used to resolve the absolute path of a package.
 * It is needed in projects that use Yarn PnP or are set up within a monorepo.
 */
function getAbsolutePath(value) {
  return dirname(require.resolve(join(value, 'package.json')));
}

const config = {
  stories: ['../src/**/*.stories.mdx', '../src/**/*.stories.@(js|jsx|ts|tsx)'],
  addons: [
    getAbsolutePath('@storybook/addon-links'),
    getAbsolutePath('@storybook/addon-essentials'),
    getAbsolutePath('@storybook/addon-mdx-gfm'),
  ],
  framework: {
    name: getAbsolutePath('@storybook/nextjs'),
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
    // console.log(path.resolve('../ui-components/src'));
    // process.exit(1);
    return {
      ...config,
      resolve: {
        ...config.resolve,
        alias: {
          ...config.resolve.alias,
          '@dagster-io/ui-components': path.resolve('../ui-components/src'),
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
    autodocs: false,
  },
  env: (config) => ({
    ...config,
    STORYBOOK: true,
  }),
};

export default config;
