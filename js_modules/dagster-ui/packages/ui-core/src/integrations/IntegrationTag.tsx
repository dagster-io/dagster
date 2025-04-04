import {IconName} from '@dagster-io/ui-components';

export enum IntegrationTag {
  Alerting = 'alerting',
  BiTools = 'bi',
  CommunitySupported = 'community-supported',
  Compute = 'compute',
  DagsterSupported = 'dagster-supported',
  EtlTools = 'etl',
  Metadata = 'metadata',
  Monitoring = 'monitoring',
  Storage = 'storage',
}

export const IntegrationTagKeys: string[] = Object.values(IntegrationTag);

export const IntegrationTagLabel: Record<IntegrationTag, string> = {
  [IntegrationTag.Alerting]: 'Alerting',
  [IntegrationTag.BiTools]: 'BI tools',
  [IntegrationTag.CommunitySupported]: 'Community Supported',
  [IntegrationTag.Compute]: 'Compute',
  [IntegrationTag.DagsterSupported]: 'Dagster Supported',
  [IntegrationTag.EtlTools]: 'ETL tools',
  [IntegrationTag.Metadata]: 'Metadata',
  [IntegrationTag.Monitoring]: 'Monitoring',
  [IntegrationTag.Storage]: 'Storage',
};

export const IntegrationTagIcon: Record<IntegrationTag, IconName> = {
  [IntegrationTag.Alerting]: 'alert',
  [IntegrationTag.BiTools]: 'chart_bar',
  [IntegrationTag.CommunitySupported]: 'people',
  [IntegrationTag.Compute]: 'speed',
  [IntegrationTag.DagsterSupported]: 'dagster_solid',
  [IntegrationTag.EtlTools]: 'transform',
  [IntegrationTag.Metadata]: 'metadata',
  [IntegrationTag.Monitoring]: 'visibility',
  [IntegrationTag.Storage]: 'download',
};
