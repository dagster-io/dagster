import {dirname, join} from 'path';
import {fileURLToPath} from 'url';

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
  framework: {
    name: getAbsolutePath('@storybook/react-vite'),
    options: {},
  },
  typescript: {
    reactDocgen: false,
  },
  viteFinal: async (config) => {
    return {
      ...config,
      logLevel: 'warn',
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
