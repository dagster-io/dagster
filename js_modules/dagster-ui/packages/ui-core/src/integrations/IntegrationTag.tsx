import {IconName} from '@dagster-io/ui-components';

export enum IntegrationTag {
  Alerting = 'alerting',
  BiTools = 'bi-tools',
  Compute = 'compute',
  DagsterSupported = 'dagster-supported',
  EtlTools = 'etl',
  Metadata = 'metadata',
  Monitoring = 'monitoring',
  Notifications = 'notifications',
  Storage = 'storage',
}

export const IntegrationTagLabel: Record<IntegrationTag, string> = {
  [IntegrationTag.Alerting]: 'Alerting',
  [IntegrationTag.BiTools]: 'BI tools',
  [IntegrationTag.Compute]: 'Compute',
  [IntegrationTag.DagsterSupported]: 'Dagster Supported',
  [IntegrationTag.EtlTools]: 'ETL tools',
  [IntegrationTag.Metadata]: 'Metadata',
  [IntegrationTag.Monitoring]: 'Monitoring',
  [IntegrationTag.Notifications]: 'Notifications',
  [IntegrationTag.Storage]: 'Storage',
};

export const IntegrationTagIcon: Record<IntegrationTag, IconName> = {
  [IntegrationTag.Alerting]: 'alert',
  [IntegrationTag.BiTools]: 'chart_bar',
  [IntegrationTag.Compute]: 'speed',
  [IntegrationTag.DagsterSupported]: 'dagster_solid',
  [IntegrationTag.EtlTools]: 'transform',
  [IntegrationTag.Metadata]: 'metadata',
  [IntegrationTag.Monitoring]: 'visibility',
  [IntegrationTag.Notifications]: 'notifications',
  [IntegrationTag.Storage]: 'download',
};
