/* eslint-disable @typescript-eslint/no-var-requires */

const redirectUrls = require('./util/redirectUrls.json');

module.exports = {
  async redirects() {
    return [
      {
        source: '/docs',
        destination: '/docs/latest',
        statusCode: 302,
      },
      {
        source: '/',
        destination: '/getting-started',
        statusCode: 302,
      },
      ...redirectUrls,
    ];
  },
  images: {
    domains: ['dagster-docs-versioned-content.s3.us-west-1.amazonaws.com'],
  },
  webpack: (config, {defaultLoaders, webpack}) => {
    config.plugins.push(
      new webpack.DefinePlugin({
        __VERSIONING_DISABLED__: process.env.VERSIONING_DISABLED === 'true',
      }),
    );

    // Add mdx loader to enable mdx import as a component
    // https://github.com/vercel/next.js/tree/canary/packages/next-mdx
    config.module.rules.push({
      test: /\.mdx/,
      use: [
        defaultLoaders.babel,
        {
          loader: '@mdx-js/loader',
        },
      ],
    });

    return config;
  },
};
