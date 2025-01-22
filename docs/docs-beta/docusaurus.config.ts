import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Dagster Docs',
  tagline: 'Dagster is a Python framework for building production-grade data platforms.',
  url: 'https://docs.dagster.io',
  favicon: 'img/favicon.ico',
  baseUrl: '/',
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'throw',
  onBrokenAnchors: 'throw',
  organizationName: 'dagster',
  projectName: 'dagster',
  markdown: {
    mermaid: true,
  },
  themes: ['@docusaurus/theme-mermaid'],
  i18n: {defaultLocale: 'en', locales: ['en']},
  plugins: [
    require.resolve('docusaurus-plugin-sass'),
    require.resolve('docusaurus-plugin-image-zoom'),
    require.resolve('./src/plugins/scoutos'),
    // NOTE: This plugin is always inactive in development and only active in production because it works on the build output.
    [
      '@docusaurus/plugin-client-redirects',
      {
        redirects: [
          {
            from: '/deployment',
            to: '/guides/deploy/',
          },
          {
            from: '/deployment/overview',
            to: '/guides/deploy/oss-deployment-architecture',
          },
          // Translated from migration spreadsheet
          // {
          //   from: '/:version(\d+.\d+.\d+)/:slug*',
          //   to: '/',
          // },
          // {
          //   from: '/dagster-cloud/:slug*',
          //   to: '/dagster-plus/',
          // },
          // {
          //   from: '/guides/dagster-pipes/:slug*',
          //   to: '/guides/build/external-pipelines/',
          // },
          {
            from: '/deploying/celery',
            to: '/guides/deploy/deployment-options/kubernetes/kubernetes-and-celery',
          },
          {
            from: '/deploying/dask',
            to: '/guides/deploy/execution/dask',
          },
          {
            from: '/deploying/airflow',
            to: '/integrations/libraries/airlift/',
          },
          {
            from: '/troubleshooting/schedules',
            to: '/guides/automate/schedules/troubleshooting-schedules',
          },
          {
            from: '/troubleshooting/run-queue',
            to: '/guides/deploy/execution/customizing-run-queue-priority',
          },
          {
            from: '/examples/airflow_ingest',
            to: '/integrations/libraries/airlift/',
          },
          {
            from: '/examples/materializations',
            to: '/guides/build/assets/',
          },
          {
            from: '/examples/conditional_execution',
            to: '/guides/build/jobs',
          },
          {
            from: '/examples/config_mapping',
            to: '/guides/operate/configuration/run-configuration',
          },
          {
            from: '/examples/dbt_example',
            to: '/integrations/libraries/dbt/',
          },
          {
            from: '/examples/dep_dsl',
            to: '/guides/build/jobs',
          },
          {
            from: '/examples/deploy_docker',
            to: '/guides/deploy/deployment-options/docker',
          },
          {
            from: '/examples/emr_pyspark',
            to: '/integrations/libraries/spark',
          },
          {
            from: '/examples/fan_in_pipeline',
            to: '/guides/build/jobs',
          },
          {
            from: '/examples/ge_example',
            to: 'https://dagster.io/blog/ensuring-data-quality-with-dagster-and-great-expectations',
          },
          {
            from: '/examples/hooks',
            to: '/guides/build/ops',
          },
          {
            from: '/examples/multi_location',
            to: '/guides/deploy/code-locations/workspace-yaml',
          },
          {
            from: '/examples/nothing',
            to: '/guides/build/jobs',
          },
          {
            from: '/examples/pipeline_tags',
            to: '/guides/build/assets/metadata-and-tags/tags',
          },
          {
            from: '/examples/basic_pyspark',
            to: '/integrations/libraries/spark',
          },
          {
            from: '/examples/dynamic_graph',
            to: '/guides/build/jobs',
          },
          {
            from: '/examples/memoized_development',
            to: '/',
          },
          {
            from: '/deployment/custom-infra/celery',
            to: '/guides/deploy/deployment-options/kubernetes/kubernetes-and-celery',
          },
          {
            from: '/deployment/custom-infra/dask',
            to: '/guides/deploy/execution/dask',
          },
          {
            from: '/deployment/custom-infra/airflow',
            to: '/guides/deploy/deployment-options/',
          },
          {
            from: '/concepts/executors',
            to: '/guides/operate/run-executors',
          },
          {
            from: '/integrations/pyspark',
            to: '/integrations/libraries/spark',
          },
          {
            from: '/deployment/guides/airflow',
            to: '/integrations/libraries/airlift/',
          },
          {
            from: '/tutorial/intro-tutorial/single-op-job',
            to: '/etl-pipeline-tutorial/',
          },
          {
            from: '/tutorial/intro-tutorial/single-solid-pipeline',
            to: '/etl-pipeline-tutorial/',
          },
          {
            from: '/tutorial/intro-tutorial/connecting-ops',
            to: '/etl-pipeline-tutorial/',
          },
          {
            from: '/tutorial/intro-tutorial/connecting-solids',
            to: '/etl-pipeline-tutorial/',
          },
          {
            from: '/tutorial/intro-tutorial/testable',
            to: '/etl-pipeline-tutorial/',
          },
          {
            from: '/tutorial/intro-tutorial/configuring-solids',
            to: '/etl-pipeline-tutorial/',
          },
          {
            from: '/tutorial/advanced-tutorial/configuring-solids',
            to: '/etl-pipeline-tutorial/',
          },
          {
            from: '/tutorial/advanced-tutorial/configuring-ops',
            to: '/etl-pipeline-tutorial/',
          },
          {
            from: '/tutorial/advanced-tutorial/pipelines',
            to: '/etl-pipeline-tutorial/',
          },
          {
            from: '/tutorial/advanced-tutorial/types',
            to: '/etl-pipeline-tutorial/',
          },
          {
            from: '/tutorial/advanced-tutorial/resources',
            to: '/etl-pipeline-tutorial/',
          },
          {
            from: '/tutorial/advanced-tutorial/repositories',
            to: '/etl-pipeline-tutorial/',
          },
          {
            from: '/tutorial/advanced-tutorial/scheduling',
            to: '/etl-pipeline-tutorial/',
          },
          {
            from: '/tutorial/advanced-tutorial/materializations',
            to: '/etl-pipeline-tutorial/',
          },
          {
            from: '/concepts/solids-pipelines/solids',
            to: '/guides/build/assets/',
          },
          {
            from: '/concepts/solids-pipelines/pipelines',
            to: '/guides/build/assets/',
          },
          {
            from: '/concepts/ops-jobs-graphs/jobs-graphs',
            to: '/guides/build/graphs',
          },
          {
            from: '/concepts/solids-pipelines/pipeline-execution',
            to: '/guides/build/assets/',
          },
          {
            from: '/concepts/solids-pipelines/composite-solids',
            to: '/guides/build/assets/',
          },
          {
            from: '/concepts/solids-pipelines/solid-events',
            to: '/guides/build/assets/',
          },
          {
            from: '/concepts/solids-pipelines/solid-hooks',
            to: '/guides/build/assets/',
          },
          {
            from: '/concepts/modes-resources',
            to: '/guides/build/external-resources/',
          },
          {
            from: '/deployment/guides/ecs',
            to: '/guides/deploy/deployment-options/aws',
          },
          // {
          //   from: '/concepts/partitions-schedules-sensors/sensors#job-failure-sensor',
          //   to: '/guides/build/sensors/testing-sensors',
          // },
          {
            from: '/integrations/dbt_cloud',
            to: '/integrations/libraries/dbt/dbt-cloud',
          },
          {
            from: '/tutorial/assets',
            to: '/guides/build/assets/',
          },
          {
            from: '/tutorial/ops-jobs/connecting-ops',
            to: '/guides/build/ops',
          },
          {
            from: '/tutorial/ops-jobs/single-op-job',
            to: '/guides/build/ops',
          },
          {
            from: '/tutorial/ops-jobs/testable',
            to: '/guides/build/ops',
          },
          {
            from: '/guides/dagster/scheduling-assets',
            to: '/guides/automate/',
          },
          {
            from: '/integrations/dbt/using-dbt-with-dagster/part-one',
            to: '/integrations/libraries/dbt/transform-dbt',
          },
          {
            from: '/integrations/dbt/using-dbt-with-dagster/part-two',
            to: '/integrations/libraries/dbt/transform-dbt',
          },
          {
            from: '/integrations/dbt/using-dbt-with-dagster/part-three',
            to: '/integrations/libraries/dbt/transform-dbt',
          },
          {
            from: '/integrations/dbt/using-dbt-with-dagster/part-four',
            to: '/integrations/libraries/dbt/transform-dbt',
          },
          {
            from: '/guides/dagster/non-argument-deps',
            to: '/guides/build/assets/defining-assets-with-asset-dependencies',
          },
          {
            from: '/tutorial/managing-your-own-io',
            to: '/guides/build/io-managers/',
          },
          {
            from: '/concepts/assets/asset-materializations',
            to: '/guides/build/assets/',
          },
          {
            from: '/getting-started/releases',
            to: '/about/releases',
          },
          {
            from: '/getting-started/telemetry',
            to: '/about/telemetry',
          },
          {
            from: '/getting-started/hello-dagster',
            to: '/',
          },
          {
            from: '/concepts/ops-jobs-graphs/metadata-tags',
            to: '/guides/build/assets/metadata-and-tags/',
          },
          {
            from: '/dagster-cloud',
            to: '/dagster-plus/',
          },
          {
            from: '/dagster-cloud/managing-deployments/setting-up-alerts',
            to: '/dagster-plus/features/alerts/',
          },
          {
            from: '/dagster-cloud/managing-deployments/dagster-cloud-cli',
            to: '/dagster-plus/deployment/management/dagster-cloud-cli/',
          },
          {
            from: '/integrations/airflow/migrating-to-dagster',
            to: '/integrations/libraries/airlift/airflow-to-dagster/',
          },
          {
            from: '/integrations/airflow/reference',
            to: '/integrations/libraries/airlift/',
          },
          {
            from: '/deployment/open-source',
            to: '/guides/deploy/',
          },
          {
            from: '/_apidocs/libraries/dagster-airflow',
            to: '/api/python-api/dagster-airlift',
          },
          {
            from: '/integrations/great-expectations',
            to: '/integrations',
          },
          {
            from: '/guides/dagster/airbyte-ingestion-as-code',
            to: '/integrations/libraries/airbyte/',
          },
          {
            from: '/integrations/databricks',
            to: '/integations/libraries/databricks',
          },
          {
            from: '/getting-started',
            to: '/',
          },
          {
            from: '/getting-started/what-why-dagster',
            to: '/',
          },
          {
            from: '/getting-started/quickstart',
            to: '/getting-started/quickstart',
          },
          {
            from: '/getting-started/install',
            to: '/getting-started/installation',
          },
          {
            from: '/getting-started/create-new-project',
            to: '/guides/build/projects/creating-a-new-project',
          },
          {
            from: '/getting-started/getting-help',
            to: '/about/community',
          },
          {
            from: '/tutorial',
            to: '/etl-pipeline-tutorial/',
          },
          {
            from: '/concepts',
            to: '/guides',
          },
          {
            from: '/concepts/assets/software-defined-assets',
            to: '/guides/build/assets/defining-assets',
          },
          {
            from: '/concepts/assets/graph-backed-assets',
            to: '/guides/build/defining-assets/#graph-asset',
          },
          {
            from: '/concepts/assets/multi-assets',
            to: '/guides/build/assets/defining-assets#multi-asset',
          },
          {
            from: '/concepts/assets/asset-jobs',
            to: '/guides/build/assets/asset-jobs',
          },
          {
            from: '/concepts/assets/asset-observations',
            to: '/guides/build/assets/metadata-and-tags/asset-observations',
          },
          {
            from: '/concepts/assets/asset-selection-syntax',
            to: '/guides/assets/asset-selection-syntax',
          },
          {
            from: '/concepts/assets/asset-checks',
            to: '/guides/test/asset-checks',
          },
          {
            from: '/concepts/assets/asset-checks/define-execute-asset-checks',
            to: '/guides/test/asset-checks',
          },
          {
            from: '/concepts/assets/asset-checks/subsetting-asset-checks',
            to: '/guides/test/running-a-subset-of-asset-checks',
          },
          {
            from: '/concepts/assets/asset-checks/checking-for-data-freshness',
            to: '/guides/test/data-freshness-testing',
          },
          {
            from: '/concepts/assets/external-assets',
            to: '/guides/build/assets/external-assets',
          },
          {
            from: '/concepts/automation',
            to: '/guides/automate/',
          },
          {
            from: '/concepts/automation/schedules',
            to: '/guides/automate/schedules/',
          },
          {
            from: '/concepts/automation/schedules/automating-assets-schedules-jobs',
            to: '/guides/automate/schedules/',
          },
          {
            from: '/concepts/automation/schedules/automating-ops-schedules-jobs',
            to: '/guides/build/ops',
          },
          {
            from: '/concepts/automation/schedules/examples',
            to: '/guides/automate/schedules/',
          },
          {
            from: '/concepts/automation/schedules/partitioned-schedules',
            to: '/guides/automate/schedules/constructing-schedules-for-partitioned-assets-and-jobs',
          },
          {
            from: '/concepts/automation/schedules/customizing-executing-timezones',
            to: '/guides/automate/schedules/customizing-execution-timezone',
          },
          {
            from: '/concepts/automation/schedules/testing',
            to: '/guides/automate/testing-schedules',
          },
          {
            from: '/concepts/automation/schedules/troubleshooting',
            to: '/guides/automate/troubleshooting-schedules',
          },
          {
            from: '/concepts/partitions-schedules-sensors/sensors',
            to: '/guides/automate/sensors/',
          },
          {
            from: '/concepts/automation/declarative-automation',
            to: '/guides/automate/declarative-automation',
          },
          {
            from: '/concepts/automation/declarative-automation/customizing-automation-conditions',
            to: '/guides/automate/declarative-automation/customizing-automation-conditions',
          },
          {
            from: '/concepts/partitions-schedules-sensors/asset-sensors',
            to: '/guides/automate/asset-sensors',
          },
          {
            from: '/concepts/partitions-schedules-sensors/partitions',
            to: '/guides/build/partitions-and-backfills/',
          },
          {
            from: '/concepts/partitions-schedules-sensors/partitioning-assets',
            to: '/guides/build/partitions-and-backfills/partitioning-assets',
          },
          {
            from: '/concepts/partitions-schedules-sensors/partitioning-ops',
            to: '/guides/build/partitions-and-backfills/partitioning-assets',
          },
          {
            from: '/concepts/partitions-schedules-sensors/testing-partitions',
            to: '/guides/test/testing-partitioned-config-and-jobs',
          },
          {
            from: '/concepts/partitions-schedules-sensors/backfills',
            to: '/guides/build/partitions-and-backfills/backfilling-data',
          },
          {
            from: '/concepts/resources',
            to: '/guides/build/external-resources',
          },
          {
            from: '/concepts/configuration/config-schema',
            to: '/guides/operate/configuration/run-configuration',
          },
          {
            from: '/concepts/configuration/advanced-config-types',
            to: '/guides/operate/configuration/advanced-config-types',
          },
          {
            from: '/concepts/code-locations',
            to: '/guides/deploy/code-locations/managing-code-locations-with-definitions',
          },
          {
            from: '/concepts/code-locations/workspace-files',
            to: '/guides/deploy/code-locations/workspace-yaml',
          },
          {
            from: '/concepts/webserver/ui-user-settings',
            to: '/guides/operate/ui-user-settings',
          },
          {
            from: '/concepts/logging',
            to: '/guides/monitor/logging/',
          },
          {
            from: '/concepts/logging/loggers',
            to: '/guides/monitor/logging/',
          },
          {
            from: '/concepts/logging/python-logging',
            to: '/guides/monitor/logging/python-logging',
          },
          {
            from: '/concepts/testing',
            to: '/guides/test/',
          },
          {
            from: '/concepts/ops-jobs-graphs/ops',
            to: '/guides/build/ops',
          },
          {
            from: '/concepts/ops-jobs-graphs/op-events',
            to: '/guides/build/ops',
          },
          {
            from: '/concepts/ops-jobs-graphs/op-hooks',
            to: '/guides/build/ops',
          },
          {
            from: '/concepts/ops-jobs-graphs/op-retries',
            to: '/guides/build/ops',
          },
          {
            from: '/concepts/ops-jobs-graphs/graphs',
            to: '/guides/build/graphs',
          },
          {
            from: '/concepts/ops-jobs-graphs/nesting-graphs',
            to: '/guides/build/graphs',
          },
          {
            from: '/concepts/ops-jobs-graphs/dynamic-graphs',
            to: '/guides/build/graphs',
          },
          {
            from: '/concepts/ops-jobs-graphs/jobs',
            to: '/guides/build/jobs',
          },
          {
            from: '/concepts/assets/asset-jobs',
            to: '/guides/build/assets/asset-jobs',
          },
          {
            from: '/concepts/ops-jobs-graphs/op-jobs',
            to: '/guides/build/jobs',
          },
          {
            from: '/concepts/ops-jobs-graphs/job-execution',
            to: '/guides/build/jobs',
          },
          {
            from: '/concepts/metadata-tags/asset-metadata',
            to: '/guides/build/assets/metadata-and-tags/',
          },
          {
            from: '/concepts/metadata-tags/asset-metadata/column-level-lineage',
            to: '/guides/build/assets/metadata-and-tags/',
          },
          {
            from: '/concepts/metadata-tags/kind-tags',
            to: '/guides/build/assets/metadata-and-tags/kind-tags',
          },
          {
            from: '/concepts/metadata-tags/op-job-metadata',
            to: '/guides/build/assets/metadata-and-tags/',
          },
          {
            from: '/concepts/metadata-tags/tags',
            to: '/guides/build/assets/metadata-and-tags/tags',
          },
          {
            from: '/concepts/dagster-pipes/subprocess',
            to: '/guides/build/external-pipelines/using-pipes/',
          },
          {
            from: '/concepts/dagster-pipes/subprocess/create-subprocess-asset',
            to: '/guides/build/external-pipelines/using-pipes/create-subprocess-asset',
          },
          {
            from: '/concepts/dagster-pipes/subprocess/modify-external-code',
            to: '/guides/build/external-pipelines/using-pipes/modify-external-code',
          },
          {
            from: '/concepts/dagster-pipes/subprocess/reference',
            to: '/guides/build/external-pipelines/using-pipes/reference',
          },
          {
            from: '/concepts/dagster-pipes/aws-ecs',
            to: '/guides/build/external-pipelines/aws-ecr-pipeline',
          },
          {
            from: '/concepts/dagster-pipes/aws-glue',
            to: '/guides/build/external-pipelines/aws-glue-pipeline',
          },
          {
            from: '/concepts/dagster-pipes/aws-emr',
            to: '/guides/build/external-pipelines/aws-emr-pipeline',
          },
          {
            from: '/concepts/dagster-pipes/aws-emr-containers',
            to: '/guides/build/external-pipelines/aws-emr-containers-pipeline',
          },
          {
            from: '/concepts/dagster-pipes/aws-emr-serverless',
            to: '/guides/build/external-pipelines/aws-emr-serverless-pipeline',
          },
          {
            from: '/concepts/dagster-pipes/aws-lambda',
            to: '/guides/build/external-pipelines/aws-lambda-pipeline',
          },
          {
            from: '/concepts/dagster-pipes/databricks',
            to: '/guides/build/external-pipelines/databricks-pipeline',
          },
          {
            from: '/concepts/dagster-pipes/kubernetes',
            to: '/guides/build/external-pipelines/kubernetes-pipeline',
          },
          {
            from: '/concepts/dagster-pipes/dagster-pipes-details-and-customization',
            to: '/guides/build/external-pipelines/dagster-pipes-details-and-customization',
          },
          {
            from: '/guides/migrations/from-step-launchers-to-pipes',
            to: '/guides/build/external-pipelines/',
          },
          {
            from: '/concepts/io-management/io-managers',
            to: 'guides/build/io-managers/',
          },
          {
            from: '/concepts/io-management/unconnected-inputs',
            to: '/guides/build/io-managers/',
          },
          {
            from: '/concepts/types',
            to: '/guides/build/assets/',
          },
          {
            from: '/concepts/logging/custom-loggers',
            to: '/guides/monitor/logging/custom-logging',
          },
          {
            from: '/concepts/webserver/graphql',
            to: '/guides/operate/graphql/',
          },
          {
            from: '/concepts/webserver/graphql-client',
            to: '/guides/operate/graphql/graphql-client',
          },
          {
            from: '/dagster-plus',
            to: '/dagster-plus/',
          },
          {
            from: '/dagster-plus/getting-started',
            to: '/dagster-plus/getting-started',
          },
          {
            from: '/dagster-plus/deployment',
            to: '/dagster-plus/deployment/deployment-types/',
          },
          {
            from: '/dagster-plus/deployment/serverless',
            to: '/dagster-plus/deployment/deployment-types/serverless/',
          },
          {
            from: '/dagster-plus/deployment/hybrid',
            to: '/dagster-plus/deployment/deployment-types/hybrid/',
          },
          {
            from: '/dagster-plus/deployment/agents',
            to: '/dagster-plus/deployment/deployment-types/hybrid/',
          },
          {
            from: '/dagster-plus/deployment/agents/amazon-ecs',
            to: '/dagster-plus/deployment/deployment-types/hybrid/amazon-ecs/',
          },
          {
            from: '/dagster-plus/deployment/agents/amazon-ecs/creating-ecs-agent-new-vpc',
            to: '/dagster-plus/deployment/deployment-types/hybrid/amazon-ecs/new-vpc',
          },
          {
            from: '/dagster-plus/deployment/agents/amazon-ecs/creating-ecs-agent-existing-vpc',
            to: '/dagster-plus/deployment/deployment-types/hybrid/amazon-ecs/existing-vpc',
          },
          {
            from: '/dagster-plus/deployment/agents/amazon-ecs/manually-provisioning-ecs-agent',
            to: '/dagster-plus/deployment/deployment-types/hybrid/amazon-ecs/manual-provision',
          },
          {
            from: '/dagster-plus/deployment/agents/amazon-ecs/configuration-reference',
            to: '/dagster-plus/deployment/deployment-types/hybrid/amazon-ecs/configuration-reference',
          },
          {
            from: '/dagster-plus/deployment/agents/amazon-ecs/upgrading-cloudformation-template',
            to: '/dagster-plus/deployment/deployment-types/hybrid/amazon-ecs/upgrading-cloudformation',
          },
          {
            from: '/dagster-plus/deployment/agents/docker',
            to: '/dagster-plus/deployment/deployment-types/hybrid/docker/',
          },
          {
            from: '/dagster-plus/deployment/agents/docker/configuring-running-docker-agent',
            to: '/dagster-plus/deployment/deployment-types/hybrid/docker/setup',
          },
          {
            from: '/dagster-plus/deployment/agents/docker/configuration-reference',
            to: '/dagster-plus/deployment/deployment-types/hybrid/docker/configuration',
          },
          {
            from: '/dagster-plus/deployment/agents/kubernetes',
            to: '/dagster-plus/deployment/deployment-types/hybrid/kubernetes/',
          },
          {
            from: '/dagster-plus/deployment/agents/kubernetes/configuring-running-kubernetes-agent',
            to: '/dagster-plus/deployment/deployment-types/hybrid/kubernetes/setup',
          },
          {
            from: '/dagster-plus/deployment/agents/kubernetes/configuration-reference',
            to: '/dagster-plus/deployment/deployment-types/hybrid/kubernetes/configuration',
          },
          {
            from: '/dagster-plus/deployment/agents/local',
            to: '/dagster-plus/deployment/deployment-types/hybrid/local',
          },
          {
            from: '/dagster-plus/deployment/agents/customizing-configuration',
            to: '/dagster-plus/deployment/management/settings/customizing-agent-settings',
          },
          {
            from: '/dagster-plus/deployment/agents/running-multiple-agents',
            to: '/dagster-plus/deployment/deployment-types/hybrid/multiple',
          },
          {
            from: '/dagster-plus/managing-deployments/setting-environment-variables-agents',
            to: '/dagster-plus/deployment/management/environment-variables/agent-config',
          },
          {
            from: '/dagster-plus/account',
            to: '/dagster-plus/deployment/management/tokens/',
          },
          {
            from: '/dagster-plus/account/managing-user-agent-tokens',
            to: '/dagster-plus/deployment/management/tokens/',
          },
          {
            from: '/dagster-plus/account/authentication',
            to: '/dagster-plus/features/authentication-and-access-control/',
          },
          {
            from: '/dagster-plus/account/managing-users',
            to: '/dagster-plus/features/authentication-and-access-control/rbac/users',
          },
          {
            from: '/dagster-plus/account/managing-users/managing-teams',
            to: '/dagster-plus/features/authentication-and-access-control/teams',
          },
          {
            from: '/dagster-plus/account/managing-users/managing-user-roles-permissions',
            to: '/dagster-plus/features/authentication-and-access-control/user-roles-permissions',
          },
          {
            from: '/dagster-plus/account/authentication/utilizing-scim-provisioning',
            to: '/dagster-plus/features/authentication-and-access-control/scim/enabling-scim-provisioning',
          },
          {
            from: '/dagster-plus/account/authentication/setting-up-azure-ad-saml-sso',
            to: '/dagster-plus/features/authentication-and-access-control/sso/azure-ad-sso',
          },
          {
            from: '/dagster-plus/account/authentication/setting-up-google-workspace-saml-sso',
            to: '/dagster-plus/features/authentication-and-access-control/sso/google-workspace-sso',
          },
          {
            from: '/dagster-plus/account/authentication/okta/saml-sso',
            to: '/dagster-plus/features/authentication-and-access-control/okta-sso',
          },
          {
            from: '/dagster-plus/account/authentication/okta/scim-provisioning',
            to: '/dagster-plus/features/authentication-and-access-control/scim/enabling-scim-provisioning',
          },
          {
            from: '/dagster-plus/account/authentication/setting-up-onelogin-saml-sso',
            to: '/dagster-plus/features/authentication-and-access-control/sso/onelogin-sso',
          },
          {
            from: '/dagster-plus/account/authentication/setting-up-pingone-saml-sso',
            to: '/dagster-plus/features/authentication-and-access-control/sso/pingone-sso',
          },
          {
            from: '/dagster-plus/managing-deployments',
            to: '/dagster-plus/deployment/management/deployments/managing-deployments',
          },
          {
            from: '/dagster-plus/managing-deployments/alerts',
            to: '/dagster-plus/features/alerts/',
          },
          {
            from: '/dagster-plus/managing-deployments/alerts/managing-alerts-in-ui',
            to: '/dagster-plus/features/alerts/creating-alerts',
          },
          {
            from: '/dagster-plus/managing-deployments/alerts/managing-alerts-cli',
            to: '/dagster-plus/features/alerts/creating-alerts',
          },
          {
            from: '/dagster-plus/managing-deployments/alerts/email',
            to: '/dagster-plus/features/alerts/configuring-an-alert-notification-service',
          },
          {
            from: '/dagster-plus/managing-deployments/alerts/microsoft-teams',
            to: '/dagster-plus/features/alerts/configuring-an-alert-notification-service',
          },
          {
            from: '/dagster-plus/managing-deployments/alerts/slack',
            to: '/dagster-plus/features/alerts/configuring-an-alert-notification-service',
          },
          {
            from: '/dagster-plus/managing-deployments/alerts/pagerduty',
            to: '/dagster-plus/features/alerts/configuring-an-alert-notification-service',
          },
          {
            from: '/dagster-plus/managing-deployments/environment-variables-and-secrets',
            to: '/dagster-plus/deployment/management/environment-variables/',
          },
          {
            from: '/dagster-plus/managing-deployments/setting-environment-variables-agents',
            to: '/dagster-plus/deployment/management/environment-variables/agent-config',
          },
          {
            from: '/dagster-plus/managing-deployments/reserved-environment-variables',
            to: '/dagster-plus/deployment/management/environment-variables/built-in',
          },
          {
            from: '/dagster-plus/managing-deployments/deployment-settings-reference',
            to: '/dagster-plus/deployment/management/deployments/deployment-settings-reference',
          },
          {
            from: '/dagster-plus/managing-deployments/code-locations',
            to: '/dagster/plus/deployment/code-locations/',
          },
          {
            from: '/dagster-plus/managing-deployments/branch-deployments',
            to: '/dagster-plus/features/ci-cd/branch-deployments/',
          },
          {
            from: '/dagster-plus/managing-deployments/branch-deployments/using-branch-deployments-with-github',
            to: '/dagster-plus/features/ci-cd/branch-deployments/setting-up-branch-deployments',
          },
          {
            from: '/dagster-plus/managing-deployments/branch-deployments/using-branch-deployments-with-gitlab',
            to: '/dagster-plus/features/ci-cd/branch-deployments/setting-up-branch-deployments',
          },
          {
            from: '/dagster-plus/managing-deployments/branch-deployments/using-branch-deployments',
            to: '/dagster-plus/features/ci-cd/branch-deployments/using-branch-deployments-with-the-cli',
          },
          {
            from: '/dagster-plus/managing-deployments/branch-deployments/change-tracking',
            to: '/dagster-plus/features/ci-cd/branch-deployments/change-tracking',
          },
          {
            from: '/dagster-plus/managing-deployments/controlling-logs',
            to: '/dagster-plus/deployment/management/managing-compute-logs-and-error-messages',
          },
          {
            from: '/dagster-plus/best-practices',
            to: '/dagster-plus/deployment/management/',
          },
          {
            from: '/dagster-plus/best-practices/managing-multiple-projects-and-teams',
            to: '/dagster-plus/deployment/management/managing-multiple-projects-and-teams',
          },
          {
            from: '/dagster-plus/insights',
            to: '/dagster-plus/features/insights/',
          },
          {
            from: '/dagster-plus/insights/asset-metadata',
            to: '/dagster-plus/features/insights/',
          },
          {
            from: '/dagster-plus/insights/integrating-external-metrics',
            to: '/dagster-plus/features/insights/',
          },
          {
            from: '/dagster-plus/insights/integrating-bigquery',
            to: '/dagster-plus/features/insights/',
          },
          {
            from: '/dagster-plus/insights/integrating-bigquery-and-dbt',
            to: '/dagster-plus/features/insights/',
          },
          {
            from: '/dagster-plus/insights/integrating-snowflake',
            to: '/dagster-plus/features/insights/',
          },
          {
            from: '/dagster-plus/insights/integrating-snowflake-and-dbt',
            to: '/dagster-plus/features/insights/',
          },
          {
            from: '/dagster-plus/insights/exporting-insights-metrics',
            to: '/dagster-plus/features/insights/',
          },
          {
            from: '/dagster-plus/managing-deployments/dagster-plus-cli',
            to: '/dagster-plus/deployment/dagster-cloud-cli',
          },
          {
            from: '/dagster-plus/references/ci-cd-file-reference',
            to: '/dagster-plus/features/ci-cd/ci-cd-file-reference',
          },
          {
            from: '/dagster-plus/managing-deployments/dagster-cloud-yaml',
            to: '/dagster-plus/deployment/dagster-cloud-yaml',
          },
          {
            from: '/dagster-plus/references/limits',
            to: '/dagster-plus/deployment/rate-limits',
          },
          {
            from: '/deployment',
            to: '/guides/deploy/',
          },
          {
            from: '/deployment/overview',
            to: '/guides/deploy/oss-deployment-architecture',
          },
          {
            from: '/deployment/concepts',
            to: '/guides/deploy/',
          },
          {
            from: '/deployment/dagster-instance',
            to: '/guides/deploy/dagster-instance-configuration',
          },
          {
            from: '/deployment/dagster-daemon',
            to: '/guides/deploy/execution/dagster-daemon',
          },
          {
            from: '/deployment/run-launcher',
            to: '/guides/deploy/execution/run-launchers',
          },
          {
            from: '/deployment/executors',
            to: '/guides/operate/run-executors',
          },
          {
            from: '/deployment/run-coordinator',
            to: '/guides/deploy/execution/run-coordinators',
          },
          {
            from: '/deployment/run-monitoring',
            to: '/guides/deploy/execution/run-monitoring',
          },
          {
            from: '/deployment/run-retries',
            to: '/guides/deploy/execution/run-retries',
          },
          {
            from: '/deployment/guides',
            to: '/guides/deploy/deployment-options/',
          },
          {
            from: '/guides/running-dagster-locally',
            to: '/guides/deploy/deployment-options/running-dagster-locally',
          },
          {
            from: '/deployment/guides/service',
            to: '/guides/deploy/deployment-options/deploying-dagster-as-a-service',
          },
          {
            from: '/deployment/guides/kubernetes',
            to: '/guides/deploy/deployment-options/kubernetes/',
          },
          {
            from: '/deployment/guides/kubernetes/deploying-with-helm',
            to: '/guides/deploy/deployment-options/kubernetes/deploying-to-kubernetes',
          },
          {
            from: '/deployment/guides/kubernetes/deploying-with-helm-advanced',
            to: '/guides/deploy/deployment-options/kubernetes/',
          },
          {
            from: '/deployment/guides/kubernetes/customizing-your-deployment',
            to: '/guides/deploy/deployment-options/kubernetes/customizing-your-deployment',
          },
          {
            from: '/deployment/guides/kubernetes/how-to-migrate-your-instance',
            to: '/guides/deploy/deployment-options/kubernetes/migrating-while-upgrading',
          },
          {
            from: '/deployment/guides/docker',
            to: '/guides/deploy/deployment-options/docker',
          },
          {
            from: '/deployment/guides/aws',
            to: '/guides/deploy/deployment-options/aws',
          },
          {
            from: '/deployment/guides/gcp',
            to: '/guides/deploy/deployment-options/gcp',
          },
          {
            from: '/deployment/guides/celery',
            to: '/guides/deploy/execution/celery',
          },
          {
            from: '/deployment/guides/dask',
            to: '/guides/deploy/execution/dask',
          },
          {
            from: '/guides/understanding-dagster-project-files',
            to: '/guides/build/projects/dagster-project-file-reference',
          },
          {
            from: '/guides/running-dagster-locally',
            to: '/guides/deploy/deployment-options/running-dagster-locally',
          },
          {
            from: '/guides/dagster/using-environment-variables-and-secrets',
            to: '/guides/deploy/using-environment-variables-and-secrets',
          },
          {
            from: '/guides/dagster/transitioning-data-pipelines-from-development-to-production',
            to: '/guides/deploy/dev-to-prod',
          },
          {
            from: '/guides/dagster/branch_deployments',
            to: '/dagster-plus/features/ci-cd/branch-deployments/testing',
          },
          {
            from: '/guides/integration/approaches-to-writing-integrations',
            to: '/integrations/guides/integration-approaches',
          },
          {
            from: '/guides/integrations/writing-a-multi-asset-decorator-integration',
            to: '/integrations/guides/multi-asset-integration',
          },
          {
            from: '/guides/dagster/how-assets-relate-to-ops-and-graphs',
            to: '/guides/build/assets',
          },
          {
            from: '/guides/dagster/enriching-with-software-defined-assets',
            to: '/guides/build/assets/',
          },
          {
            from: '/guides/dagster/software-defined-assets',
            to: '/guides/build/assets/',
          },
          {
            from: '/guides/dagster/testing-assets',
            to: '/guides/test/unit-testing-assets-and-ops',
          },
          {
            from: '/guides/dagster/migrating-to-pythonic-resources-and-config',
            to: '/guides/operate/configuration/run-configuration',
          },
          {
            from: '/guides/dagster/intro-to-ops-jobs',
            to: '/guides/build/ops',
          },
          {
            from: '/guides/dagster/intro-to-ops-jobs/single-op-job',
            to: '/guides/build/ops',
          },
          {
            from: '/guides/dagster/intro-to-ops-jobs/testable',
            to: '/guides/build/ops',
          },
          {
            from: '/guides/dagster/intro-to-ops-jobs/connecting-ops',
            to: '/guides/build/ops',
          },
          {
            from: '/0.15.7/guides/dagster/graph_job/op',
            to: '/guides/build/ops',
          },
          {
            from: '/guides/dagster/re-execution',
            to: '/guides/build/ops',
          },
          {
            from: '/migration',
            to: '/guides/migrate/',
          },
          {
            from: '/guides/migrations',
            to: '/guides/migrate/',
          },
          {
            from: '/integrations/airflow/from-airflow-to-dagster',
            to: '/integrations/libraries/airlift/airflow-to-dagster',
          },
          {
            from: '/guides/migrations/observe-your-airflow-pipelines-with-dagster',
            to: '/integrations/libraries/airlift/',
          },
          {
            from: '/guides/dagster/recommended-project-structure',
            to: '/guides/build/project-structure/',
          },
          {
            from: '/guides/dagster/ml-pipeline',
            to: '/guides/build/ml-pipelines',
          },
          {
            from: '/guides/dagster/managing-ml',
            to: '/guides/build/ml-pipelines',
          },
          {
            from: '/guides/dagster/example_project',
            to: '/etl-pipeline-tutorial/',
          },
          {
            from: '/guides/experimental-features',
            to: '/',
          },
          {
            from: '/guides/limiting-concurrency-in-data-pipelines',
            to: '/guides/operate/managing-concurrency',
          },
          {
            from: '/guides/customizing-run-queue-priority',
            to: '/guides/deploy/execution/customizing-run-coordinator-priority',
          },
          {
            from: '/guides/dagster/dagster_type_factories',
            to: '/guides/build/assets/',
          },
          {
            from: '/guides/dagster/asset-versioning-and-caching',
            to: '/guides/build/assets/asset-versioning-and-caching',
          },
          {
            from: '/guides/dagster/code-references',
            to: '/guides/build/assets/metadata-and-tags/',
          },
          {
            from: '/integrations/airbyte',
            to: '/integrations/libraries/airbyte/',
          },
          {
            from: '/integrations/airbyte-cloud',
            to: '/integrations/libraries/airbyte/airbyte-cloud',
          },
          {
            from: '/integrations/airflow',
            to: '/integrations/libraries/airlift/',
          },
          {
            from: '/concepts/dagster-pipes/databricks',
            to: '/guides/build/external-pipelines/databricks-pipeline',
          },
          {
            from: '/integrations/dbt',
            to: '/integrations/libraries/dbt/',
          },
          {
            from: '/integrations/dbt/quickstart',
            to: '/integrations/libraries/dbt/transform-dbt',
          },
          {
            from: '/integrations/dbt/using-dbt-with-dagster',
            to: '/integrations/libraries/dbt/using-dbt-with-dagster',
          },
          {
            from: '/integrations/dbt/using-dbt-with-dagster/set-up-dbt-project',
            to: '/integrations/libraries/dbt/using-dbt-with-dagster/set-up-dbt-project',
          },
          {
            from: '/integrations/dbt/using-dbt-with-dagster/load-dbt-models',
            to: '/integrations/libraries/dbt/using-dbt-with-dagster/load-dbt-models',
          },
          {
            from: '/integrations/dbt/using-dbt-with-dagster/upstream-assets',
            to: '/integrations/libraries/dbt/using-dbt-with-dagster/upstream-assets',
          },
          {
            from: '/integrations/dbt/using-dbt-with-dagster/downstream-assets',
            to: '/integrations/libraries/dbt/using-dbt-with-dagster/downstream-assets',
          },
          {
            from: '/integrations/dbt/using-dbt-with-dagster-plus',
            to: '/integrations/libraries/dbt/using-dbt-with-dagster-plus/',
          },
          {
            from: '/integrations/dbt/using-dbt-with-dagster-plus/serverless',
            to: '/integrations/libraries/dbt/using-dbt-with-dagster-plus/serverless',
          },
          {
            from: '/integrations/dbt/using-dbt-with-dagster-plus/hybrid',
            to: '/integrations/libraries/dbt/using-dbt-with-dagster-plus/hybrid',
          },
          {
            from: '/integrations/dbt/reference',
            to: '/integrations/libraries/dbt/reference',
          },
          {
            from: '/integrations/dbt-cloud',
            to: '/integrations/libraries/dbt/dbt-cloud',
          },
          {
            from: '/integrations/deltalake',
            to: '/integrations/libraries/deltalake',
          },
          {
            from: '/integrations/deltalake/using-deltalake-with-dagster',
            to: '/integrations/libraries/deltalake',
          },
          {
            from: '/integrations/deltalake/reference',
            to: '/integrations/libraries/deltalake',
          },
          {
            from: '/integrations/duckdb',
            to: '/integrations/libraries/duckdb',
          },
          {
            from: '/integrations/duckdb/using-duckdb-with-dagster',
            to: '/integrations/libraries/duckdb',
          },
          {
            from: '/integrations/duckdb/reference',
            to: '/integrations/libraries/duckdb',
          },
          {
            from: '/integrations/embedded-elt',
            to: '/integrations/libraries/embedded-elt',
          },
          {
            from: '/integrations/embedded-elt/dlt',
            to: '/integrations/libraries/dlt',
          },
          {
            from: '/integrations/embedded-elt/sling',
            to: '/integrations/libraries/sling',
          },
          {
            from: '/integrations/fivetran',
            to: '/integrations/libraries/fivetran',
          },
          {
            from: '/integrations/bigquery',
            to: '/integrations/libraries/gcp/bigquery',
          },
          {
            from: '/integrations/bigquery/using-bigquery-with-dagster',
            to: '/integrations/libraries/gcp/bigquery',
          },
          {
            from: '/integrations/bigquery/reference',
            to: '/integrations/libraries/gcp/bigquery',
          },
          {
            from: '/integrations/dagstermill',
            to: '/integrations/libraries/jupyter',
          },
          {
            from: '/integrations/dagstermill/using-notebooks-with-dagster',
            to: '/integrations',
          },
          {
            from: '/integrations/dagstermill/reference',
            to: '/integrations',
          },
          {
            from: '/integrations/looker',
            to: '/integrations/libraries/looker',
          },
          {
            from: '/integrations/openai',
            to: '/integrations/libraries/openai',
          },
          {
            from: '/integrations/pandas',
            to: '/integrations/libraries/pandas',
          },
          {
            from: '/integrations/pandera',
            to: '/integrations/libraries/pandera',
          },
          {
            from: '/integrations/powerbi',
            to: '/integrations/libraries/powerbi',
          },
          {
            from: '/integrations/sigma',
            to: '/integrations/libraries/sigma',
          },
          {
            from: '/integrations/spark',
            to: '/integrations/libraries/spark',
          },
          {
            from: '/integrations/snowflake',
            to: '/integrations/libraries/snowflake',
          },
          {
            from: '/integrations/snowflake/using-snowflake-with-dagster',
            to: '/integrations/libraries/snowflake',
          },
          {
            from: '/integrations/snowflake/using-snowflake-with-dagster-io-managers',
            to: '/integrations/libraries/snowflake',
          },
          {
            from: '/integrations/snowflake/reference',
            to: '/integrations/libraries/snowflake',
          },
          {
            from: '/integrations/tableau',
            to: '/integrations/libraries/tableau',
          },
        ],
        createRedirects(existingPath) {
          if (existingPath.includes('/api/python-api')) {
            return [existingPath.replace('/api/python-api', '/_apidocs')];
          }
          return undefined; // Return a falsy value: no redirect created
        },
      },
    ],
  ],
  themeConfig: {
    // Algolia environment variables are not required during development
    algolia:
      process.env.NODE_ENV === 'development'
        ? {
            appId: 'ABC123',
            apiKey: 'ABC123',
            indexName: 'ABC123',
            contextualSearch: false,
          }
        : {
            appId: process.env.ALGOLIA_APP_ID,
            apiKey: process.env.ALGOLIA_API_KEY,
            indexName: process.env.ALGOLIA_INDEX_NAME,
            contextualSearch: false,
          },
    announcementBar: {
      id: 'announcementBar',
      content: `<div><h3>Welcome to Dagster's new and improved documentation site!</h3> You can find the legacy documentation with content for versions 1.9.8 and earlier at <a target="_blank" href="https://legacy-docs.dagster.io/">legacy-docs.dagster.io</a>.</div>`,
    },
    colorMode: {
      defaultMode: 'light',
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['diff', 'json', 'bash', 'docker'],
    },
    zoom: {
      selector: '.markdown > img, .tabs-container img ',
      config: {
        // options you can specify via https://github.com/francoischalifour/medium-zoom#usage
        background: {
          light: 'rgb(255, 255, 255)',
          dark: 'rgb(50, 50, 50)',
        },
      },
    },
    tableOfContents: {
      minHeadingLevel: 2,
      maxHeadingLevel: 4,
    },
    navbar: {
      hideOnScroll: true,
      logo: {
        alt: 'Dagster Logo',
        src: 'img/dagster-docs-logo.svg',
        srcDark: 'img/dagster-docs-logo-dark.svg',
        href: '/',
      },
      items: [
        {
          label: 'Docs',
          type: 'doc',
          docId: 'intro',
          position: 'left',
        },
        //{
        //  label: 'Tutorials',
        //  type: 'doc',
        //  docId: 'tutorials/index',
        //  position: 'left',
        //},
        {
          label: 'Integrations',
          type: 'doc',
          docId: 'integrations/libraries/index',
          position: 'left',
        },
        {
          label: 'Dagster+',
          type: 'doc',
          docId: 'dagster-plus/index',
          position: 'left',
        },
        {
          label: 'API reference',
          type: 'doc',
          docId: 'api/index',
          position: 'left',
        },
        //{
        //  label: 'Changelog',
        //  type: 'doc',
        //  docId: 'changelog',
        //  position: 'right',
        //},
        {
          label: 'Feedback',
          href: 'https://github.com/dagster-io/dagster/discussions/24816',
          position: 'right',
          className: 'feedback-nav-link',
        },
      ],
    },
    image: 'img/docusaurus-social-card.jpg',
    docs: {
      sidebar: {
        autoCollapseCategories: false,
        hideable: false,
      },
    },

    footer: {
      logo: {
        alt: 'Dagster Logo',
        src: 'img/dagster_labs-primary-horizontal.svg',
        srcDark: 'img/dagster_labs-reversed-horizontal.svg',
        href: '/',
      },
      links: [
        {
          html: `
          <div class='footer__items'>
            <a href='https://www.dagster.io/terms'>Terms of Service</a>
            <a href='https://www.dagster.io/privacy/'>Privacy Policy</a>
            <a href='https://www.dagster.io/security/'>Security</a>
          </div>

          <div class='footer__items--right'>
            <a href='https://twitter.com/dagster' title="X" target="_blank" rel="noreferrer noopener"><img src="/icons/twitter.svg"/></a>
            <a href='https://www.dagster.io/slack/' title="Community Slack" target="_blank" rel="noreferrer noopener"><img src="/icons/slack.svg"/></a>
            <a href='https://github.com/dagster-io/dagster' title="GitHub" target="_blank" rel="noreferrer noopener"><img src="/icons/github.svg"/></a>
            <a href='https://www.youtube.com/channel/UCfLnv9X8jyHTe6gJ4hVBo9Q/videos' title="Youtube" target="_blank" rel="noreferrer noopener"><img src="/icons/youtube.svg"/></a>
          </div>
          `,
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Dagster Labs`,
    },
  } satisfies Preset.ThemeConfig,

  presets: [
    [
      '@docusaurus/preset-classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: '/',
          editUrl: 'https://github.com/dagster-io/dagster/tree/master/docs/docs-beta',
        },
        blog: false,
        theme: {
          customCss: [
            require.resolve('./node_modules/modern-normalize/modern-normalize.css'),
            require.resolve('./src/styles/custom.scss'),
          ],
        },
        // https://docusaurus.io/docs/api/plugins/@docusaurus/plugin-sitemap#ex-config
        sitemap: {
          //lastmod: 'date',
          changefreq: 'weekly',
          priority: 0.5,
          ignorePatterns: ['/tags/**'],
          filename: 'sitemap.xml',
          createSitemapItems: async (params) => {
            const {defaultCreateSitemapItems, ...rest} = params;
            const items = await defaultCreateSitemapItems(rest);
            //return items.filter((item) => !item.url.includes('/page/'));
            return items;
          },
        },
      } satisfies Preset.Options,
    ],
  ],
};

export default config;
