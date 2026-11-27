import {routes, type VercelConfig} from '@vercel/config/v1';

const oldDocsHost = {has: [{type: 'host' as const, value: 'docs.dagster.io'}]};

export const config: VercelConfig = {
  buildCommand: "echo 'Starting build...' && yarn build-api-docs && yarn build-kinds-tags && yarn build",
  cleanUrls: true,
  trailingSlash: false,
  /**
   * The redirects directory contains JSON files of server-side redirects handled by Vercel.
   * These files are organized by destination, e.g., guides.json contains redirects TO
   * destination URLs that start with `/docs/guides`.
   */
  bulkRedirectsPath: 'redirects',
  // The site is served under dagster.io/docs, but Docusaurus emits files at the build root.
  rewrites: [routes.rewrite('/docs/:path*', '/:path*')],
  redirects: [
    // `/:path*` doesn't catch `/`, and paths already under `/docs` must not get a second prefix.
    routes.redirect('/', 'https://dagster.io/docs', oldDocsHost),
    routes.redirect('/docs', 'https://dagster.io/docs', oldDocsHost),
    routes.redirect('/docs/:path*', 'https://dagster.io/docs/:path*', oldDocsHost),
    routes.redirect('/:path*', 'https://dagster.io/docs/:path*', oldDocsHost),
    routes.redirect('/', '/docs'),

    /**
    The redirects below CANNOT be placed in bulk redirect JSON files in the /redirects folder,
    since they use wildcard and/or header matching.
    For redirect formatting and examples, see
    https://vercel.com/docs/project-configuration/vercel-ts?package-manager=yarn#redirects
    Note that the use of 'to' and 'from' in the Vercel docs is confusing.
    The format is routes.redirect('source', 'destination')
    Redirects below are organized by destination.
    Also note that in this file, redirects are permanent (status code 308) by default,
    but in bulk redirect files, they are temporary (307) by default.
    */

    // USER GUIDE (/guides)
    routes.redirect('/docs/dagster-cloud/insights/:path*', '/docs/guides/observe/insights/:path*'),
    routes.redirect('/docs/next/guides/build/components/:path', '/docs/guides/build/components/:path'),
    routes.redirect('/docs/guides/preview/:path*', '/docs/guides/labs/:path*'),
    routes.redirect('/docs/dagster-plus/features/insights/:path*', '/docs/guides/observe/insights/:path*'),
    routes.redirect('/docs/dagster-plus/features/alerts/:path*', '/docs/guides/observe/alerts/:path*'),
    routes.redirect('/docs/guides/labs/components/:path*', '/docs/guides/build/components/:path*'),
    routes.redirect('/docs/guides/monitor/insights/:path*', '/docs/guides/observe/insights/:path*'),
    routes.redirect('/docs/guides/monitor/alerts/:path*', '/docs/guides/observe/alerts/:path*'),
    routes.redirect('/docs/guides/monitor/logging/:path*', '/docs/guides/log-debug/logging/:path*'),

    // EXAMPLES
    routes.redirect('/docs/tutorials/:path*', '/docs/examples/:path*'),
    routes.redirect('/docs/tutorials/:path*/', '/docs/examples/:path*'),
    routes.redirect(
      '/docs/integrations/guides/:path*',
      '/docs/guides/build/components/creating-new-components/creating-and-registering-a-component',
    ),
    routes.redirect('/docs/guides/build/ml-pipelines/:path*', '/docs/examples/full-pipelines/ml'),
    routes.redirect('/docs/examples/bluesky/:path*', '/docs/examples/full-pipelines/bluesky/:path*'),
    routes.redirect('/docs/examples/dbt/:path*', '/docs/examples/full-pipelines/dbt/:path*'),
    routes.redirect('/docs/examples/dspy/:path*', '/docs/examples/full-pipelines/dspy/:path*'),
    routes.redirect('/docs/examples/etl-pipeline/:path*', '/docs/examples/full-pipelines/etl-pipeline/:path*'),
    routes.redirect('/docs/examples/llm-fine-tuning/:path*', '/docs/examples/full-pipelines/llm-fine-tuning/:path*'),
    routes.redirect('/docs/examples/ml/:path*', '/docs/examples/full-pipelines/ml/:path*'),
    routes.redirect('/docs/examples/modal/:path*', '/docs/examples/full-pipelines/modal/:path*'),
    routes.redirect(
      '/docs/examples/prompt-engineering/:path*',
      '/docs/examples/full-pipelines/prompt-engineering/:path*',
    ),
    routes.redirect('/docs/examples/rag/:path*', '/docs/examples/full-pipelines/rag/:path*'),
    routes.redirect('/docs/examples/reference-architectures/:path*', '/docs/examples'),
    routes.redirect('/docs/examples/mini-examples/:path*', '/docs/examples/best-practices/:path*'),

    // DEPLOYMENT
    routes.redirect('/docs/dagster-cloud/:path*', '/docs/deployment/dagster-plus/:path*'),
    routes.redirect(
      '/docs/dagster-plus/features/authentication-and-access-control/:path*',
      '/docs/deployment/dagster-plus/authentication-and-access-control/:path*',
    ),
    routes.redirect('/docs/guides/deploy/deployment-options/:path*', '/docs/deployment/oss/deployment-options/:path*'),
    routes.redirect('/docs/guides/deploy/execution/:path*', '/docs/deployment/execution/:path*'),
    routes.redirect(
      '/docs/dagster-plus/deployment/management/:path*',
      '/docs/deployment/dagster-plus/management/:path*',
    ),
    routes.redirect('/docs/dagster-plus/deployment/azure/:path*', '/docs/deployment/dagster-plus/hybrid/azure/:path*'),
    routes.redirect(
      '/docs/dagster-plus/features/ci-cd/:path*',
      '/docs/deployment/dagster-plus/deploying-code/configuring-ci-cd',
    ),
    routes.redirect(
      '/docs/dagster-plus/deployment/deployment-types/serverless/:path*',
      '/docs/deployment/dagster-plus/serverless/:path*',
    ),
    routes.redirect(
      '/docs/dagster-plus/deployment/deployment-types/hybrid/:path*',
      '/docs/deployment/dagster-plus/hybrid/:path*',
    ),
    routes.redirect(
      '/docs/deployment/dagster-plus/serverless/run-isolation',
      '/docs/deployment/dagster-plus/run-isolation',
    ),

    // MIGRATION
    routes.redirect('/docs/guides/migrate/:path*', '/docs/migration/:path*'),

    // INTEGRATIONS
    routes.redirect('/docs/guides/dagster-pipes/:path*', '/docs/integrations/external-pipelines'),
    routes.redirect('/docs/_apidocs/libraries/:path*', '/docs/integrations/libraries/:path*'),
    routes.redirect('/docs/guides/build/external-pipelines/:path*', '/docs/integrations/external-pipelines/:path*'),
    routes.redirect(
      '/docs/integrations/libraries/dbt/using-dbt-with-dagster/:path*',
      '/docs/integrations/libraries/dbt',
    ),
    routes.redirect(
      '/docs/integrations/dbt/using-dbt-with-dagster-plus/:path*',
      '/docs/integrations/libraries/dbt/using-dbt-with-dagster-plus/:path*',
    ),
    routes.redirect('/docs/api/python-api/libraries/:path*', '/docs/integrations/libraries/:path*'),
    routes.redirect(
      '/docs/integrations/libraries/dbt/creating-a-dbt-project-in-dagster/:path*',
      '/docs/integrations/libraries/dbt',
    ),
    routes.redirect('/docs/integrations/snowflake/:path*', '/docs/integrations/libraries/snowflake/:path*'),

    // API
    routes.redirect('/docs/sections/api/apidocs/:path*/', '/docs/api'),
    routes.redirect('/docs/sections/api/apidocs/:path*', '/docs/api'),
    routes.redirect('/docs/docs/apidocs/:path*', '/docs/api'),
    routes.redirect('/docs/master/_apidocs/:path*', '/docs/api'),
    routes.redirect('/docs/_apidocs/:path*', '/docs/api/dagster/:path*'),

    // MISC
    routes.redirect('/docs/next/:path*', '/docs/:path*'),
    routes.redirect('/docs/next/:path*/', '/docs/:path*'),
    routes.redirect(
      '/docs/examples/ge_example',
      'https://dagster.io/blog/ensuring-data-quality-with-dagster-and-great-expectations',
    ),
    routes.redirect('/docs/guides/labs/dagster-mcp', '/docs/getting-started/ai-tools/dagster-mcp'),
    routes.redirect('/docs/changelog', '/docs/about/changelog', {
      has: [
        {
          type: 'query',
          key: 'page',
        },
      ],
    }),
  ],
};
