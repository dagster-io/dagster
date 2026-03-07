import path, {dirname, join} from 'path';
import {fileURLToPath} from 'url';
import graphql from '@rollup/plugin-graphql';

/**
 * This function is used to resolve the absolute path of a package.
 * It is needed in projects that use Yarn PnP or are set up within a monorepo.
 */
function getAbsolutePath(value) {
  return dirname(fileURLToPath(import.meta.resolve(join(value, 'package.json'))));
}

const config = {
  stories: ['../src/**/*.stories.tsx'],
  addons: [
    getAbsolutePath('@storybook/addon-themes'),
    getAbsolutePath('@storybook/addon-links'),
    getAbsolutePath('@chromatic-com/storybook'),
    getAbsolutePath('@storybook/addon-docs'),
  ],
  typescript: {
    reactDocgen: false,
  },
  framework: {
    name: getAbsolutePath('@storybook/react-vite'),
  },
  // Vite configuration for aliases and GraphQL support
  viteFinal: async (config) => {
    return {
      ...config,
      logLevel: 'warn',
      plugins: [...(config.plugins || []), graphql()],
      build: {
        ...config.build,
        // Disable asset inlining - Icon component uses CSS masks which require file paths
        assetsInlineLimit: 0,
        rollupOptions: {
          ...config.build?.rollupOptions,
          onwarn(warning, warn) {
            if (warning.code === 'MODULE_LEVEL_DIRECTIVE' && warning.message.includes('"use client"')) {
              return;
            }
            warn(warning);
          },
        },
      },
      resolve: {
        ...config.resolve,
        alias: {
          ...config.resolve?.alias,
          '@dagster-io/ui-components': path.resolve('../ui-components/src'),
          '@dagster-io/dg-docs-components': path.resolve('../dg-docs-components/src'),
          '@shared': path.resolve('./src/shared'),
        },
      },
    };
  },
  docs: {},
  env: (config) => ({
    ...config,
    STORYBOOK: true,
  }),
};

// eslint-disable-next-line import/no-default-export
export default config;
