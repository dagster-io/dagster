import {routes, type VercelConfig} from '@vercel/config/v1';

export const config: VercelConfig = {
  buildCommand: "echo 'Starting build...' && yarn build-api-docs && yarn build-kinds-tags && yarn build",
  cleanUrls: true,
  trailingSlash: false,
  bulkRedirectsPath: 'redirects',
  redirects: [
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
    routes.redirect('/dagster-cloud/insights/:path*', '/guides/observe/insights/:path*'),
    routes.redirect('/next/guides/build/components/:path', '/guides/build/components/:path'),
    routes.redirect('/guides/preview/:path*', '/guides/labs/:path*'),
    routes.redirect('/dagster-plus/features/insights/:path*', '/guides/observe/insights/:path*'),
    routes.redirect('/dagster-plus/features/alerts/:path*', '/guides/observe/alerts/:path*'),
    routes.redirect('/guides/labs/components/:path*', '/guides/build/components/:path*'),
    routes.redirect('/guides/monitor/insights/:path*', '/guides/observe/insights/:path*'),
    routes.redirect('/guides/monitor/alerts/:path*', '/guides/observe/alerts/:path*'),
    routes.redirect('/guides/monitor/logging/:path*', '/guides/log-debug/logging/:path*'),

    // EXAMPLES
    routes.redirect('/tutorials/:path*', '/examples/:path*'),
    routes.redirect('/tutorials/:path*/', '/examples/:path*'),
    routes.redirect(
      '/integrations/guides/:path*',
      '/guides/build/components/creating-new-components/creating-and-registering-a-component',
    ),
    routes.redirect('/guides/build/ml-pipelines/:path*', '/examples/ml'),
    routes.redirect('/examples/bluesky/:path*', '/examples/full-pipelines/bluesky/:path*'),
    routes.redirect('/examples/dbt/:path*', '/examples/full-pipelines/dbt/:path*'),
    routes.redirect('/examples/etl-pipeline/:path*', '/examples/full-pipelines/etl-pipeline/:path*'),
    routes.redirect('/examples/llm-fine-tuning/:path*', '/examples/full-pipelines/llm-fine-tuning/:path*'),
    routes.redirect('/examples/modal/:path*', '/examples/full-pipelines/modal/:path*'),
    routes.redirect('/examples/prompt-engineering/:path*', '/examples/full-pipelines/prompt-engineering/:path*'),
    routes.redirect('/examples/rag/:path*', '/examples/full-pipelines/rag/:path*'),
    routes.redirect('/examples/reference-architectures/:path*', '/examples'),
    routes.redirect('/examples/mini-examples/:path*', '/examples/best-practices/:path*'),

    // DEPLOYMENT
    routes.redirect('/dagster-cloud/:path*', '/deployment/dagster-plus/:path*'),
    routes.redirect(
      '/dagster-plus/features/authentication-and-access-control/:path*',
      '/deployment/dagster-plus/authentication-and-access-control/:path*',
    ),
    routes.redirect('/guides/deploy/deployment-options/:path*', '/deployment/oss/deployment-options/:path*'),
    routes.redirect('/guides/deploy/execution/:path*', '/deployment/execution/:path*'),
    routes.redirect('/dagster-plus/deployment/management/:path*', '/deployment/dagster-plus/management/:path*'),
    routes.redirect('/dagster-plus/deployment/azure/:path*', '/deployment/dagster-plus/hybrid/azure/:path*'),
    routes.redirect('/dagster-plus/features/ci-cd/:path*', '/deployment/dagster-plus/deploying-code/configuring-ci-cd'),
    routes.redirect(
      '/dagster-plus/deployment/deployment-types/serverless/:path*',
      '/deployment/dagster-plus/serverless/:path*',
    ),
    routes.redirect(
      '/dagster-plus/deployment/deployment-types/hybrid/:path*',
      '/deployment/dagster-plus/hybrid/:path*',
    ),
    routes.redirect('/deployment/dagster-plus/serverless/run-isolation', '/deployment/dagster-plus/run-isolation'),

    // MIGRATION
    routes.redirect('/guides/migrate/:path*', '/migration/:path*'),

    // INTEGRATIONS
    routes.redirect('/guides/dagster-pipes/:path*', '/integrations/external-pipelines'),
    routes.redirect('/_apidocs/libraries/:path*', '/integrations/libraries/:path*'),
    routes.redirect('/guides/build/external-pipelines/:path*', '/integrations/external-pipelines/:path*'),
    routes.redirect('/integrations/libraries/dbt/using-dbt-with-dagster/:path*', '/integrations/libraries/dbt'),
    routes.redirect(
      '/integrations/dbt/using-dbt-with-dagster-plus/:path*',
      '/integrations/libraries/dbt/using-dbt-with-dagster-plus/:path*',
    ),
    routes.redirect('/api/python-api/libraries/:path*', '/integrations/libraries/:path*'),
    routes.redirect(
      '/integrations/libraries/dbt/creating-a-dbt-project-in-dagster/:path*',
      '/integrations/libraries/dbt',
    ),
    routes.redirect('/integrations/snowflake/:path*', '/integrations/libraries/snowflake/:path*'),

    // API
    routes.redirect('/sections/api/apidocs/:path*/', '/api'),
    routes.redirect('/sections/api/apidocs/:path*', '/api'),
    routes.redirect('/docs/apidocs/:path*', '/api'),
    routes.redirect('/master/_apidocs/:path*', '/api'),
    routes.redirect('_apidocs/:path*', '/api/dagster/:path*'),

    // ABOUT
    routes.redirect('/getting-started/:path*', '/about/:path*'),

    // MISC
    routes.redirect('/next/:path*', '/:path*'),
    routes.redirect('/next/:path*/', '/:path*'),
    routes.redirect(
      '/examples/ge_example',
      'https://dagster.io/blog/ensuring-data-quality-with-dagster-and-great-expectations',
    ),
    routes.redirect('/changelog', '/about/changelog', {
      has: [
        {
          type: 'query',
          key: 'page',
        },
      ],
    }),
  ],
};
