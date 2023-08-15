import {dirname, join} from 'path';

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
    name: getAbsolutePath('@storybook/react-webpack5'),
    options: {},
  },
  // https://github.com/hipstersmoothie/react-docgen-typescript-plugin/issues/78#issuecomment-1409224863
  typescript: {
    reactDocgen: 'react-docgen-typescript-plugin',
  },
  // https://storybook.js.org/docs/react/configure/webpack#bundle-splitting
  features: {
    storyStoreV7: true,
  },
  docs: {
    autodocs: true,
  },
  env: (config) => ({
    ...config,
    STORYBOOK: true,
  }),
};

export default config;
