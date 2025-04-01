import {Box, Colors} from '@dagster-io/ui-components';
import {Meta} from '@storybook/react';

import {IntegrationTag} from '../IntegrationTag';
import {MarketplaceHome} from '../MarketplaceHome';
import {IntegrationConfig} from '../types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Integrations/MarketplaceHome',
  component: MarketplaceHome,
} as Meta;

export const Default = () => {
  const integrations: IntegrationConfig[] = [
    {
      id: 'airbyte',
      name: 'Airbyte',
      icon: 'airbyte',
      tags: [IntegrationTag.EltTools],
    },
    {
      id: 'aws',
      name: 'AWS',
      icon: 'aws',
      tags: [IntegrationTag.Storage, IntegrationTag.Compute],
    },
    {
      id: 'azure',
      name: 'Azure',
      icon: 'azure',
      tags: [IntegrationTag.Storage, IntegrationTag.Compute],
    },
    {
      id: 'bigquery',
      name: 'BigQuery',
      icon: 'bigquery',
      tags: [IntegrationTag.Storage],
    },
    {
      id: 'dbt',
      name: 'dbt',
      icon: 'dbt',
      tags: [IntegrationTag.EltTools],
    },
    {
      id: 'duckdb',
      name: 'DuckDB',
      icon: 'duckdb',
      tags: [IntegrationTag.Storage],
    },
    {
      id: 'fivetran',
      name: 'Fivetran',
      icon: 'fivetran',
      tags: [IntegrationTag.EltTools],
    },
    {
      id: 'gcp',
      name: 'Google Cloud Platform',
      icon: 'gcp',
      tags: [IntegrationTag.Storage, IntegrationTag.Compute],
    },
    {
      id: 'great-expectations',
      name: 'Great Expectations',
      icon: 'greatexpectations',
      tags: [IntegrationTag.Monitoring],
    },
    {
      id: 'jupyter',
      name: 'Jupyter',
      icon: 'jupyter',
      tags: [IntegrationTag.BiTools],
    },
    {
      id: 'mlflow',
      name: 'MLflow',
      icon: 'mlflow',
      tags: [IntegrationTag.Metadata],
    },
    {
      id: 'noteable',
      name: 'Noteable',
      icon: 'noteable',
      tags: [IntegrationTag.BiTools],
    },
    {
      id: 'pandas',
      name: 'pandas',
      icon: 'pandas',
      tags: [IntegrationTag.EltTools],
    },
    {
      id: 'pyspark',
      name: 'PySpark',
      icon: 'pyspark',
      tags: [IntegrationTag.Compute],
    },
    {
      id: 'redshift',
      name: 'Redshift',
      icon: 'redshift',
      tags: [IntegrationTag.Storage],
    },
    {
      id: 'sling',
      name: 'Sling',
      icon: 'sling',
      tags: [IntegrationTag.EltTools],
    },
    {
      id: 'snowflake',
      name: 'Snowflake',
      icon: 'snowflake',
      tags: [IntegrationTag.Storage],
    },
  ];

  return (
    <Box padding={64} style={{width: '1300px', backgroundColor: Colors.backgroundLight()}}>
      <MarketplaceHome integrations={integrations} />
    </Box>
  );
};
