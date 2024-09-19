import path, {dirname, join} from 'path';

/**
 * This function is used to resolve the absolute path of a package.
 * It is needed in projects that use Yarn PnP or are set up within a monorepo.
 */
function getAbsolutePath(value) {
  return dirname(require.resolve(join(value, 'package.json')));
}

const config = {
  stories: ['../src/**/*.stories.tsx'],
  addons: [
    getAbsolutePath('@storybook/addon-themes'),
    getAbsolutePath('@storybook/addon-links'),
    getAbsolutePath('@storybook/addon-essentials'),
    getAbsolutePath('@chromatic-com/storybook'),
  ],
  typescript: {
    reactDocgen: false,
  },
  framework: {
    name: getAbsolutePath('@storybook/nextjs'),
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
          {
            test: /\.(graphql|gql)$/,
            exclude: /node_modules/,
            loader: 'graphql-tag/loader',
          },
        ],
      },
    };
  },
  docs: {},
  env: (config) => ({
    ...config,
    STORYBOOK: true,
  }),
};

export default config;
