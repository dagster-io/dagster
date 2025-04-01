import {IconName} from '@dagster-io/ui-components';

export enum IntegrationTag {
  Alerting = 'alerting',
  BiTools = 'bi-tools',
  ComponentReady = 'component-ready',
  Compute = 'compute',
  EltTools = 'elt-tools',
  Metadata = 'metadata',
  Monitoring = 'monitoring',
  Notifications = 'notifications',
  Storage = 'storage',
}

export const IntegrationTagLabel: Record<IntegrationTag, string> = {
  [IntegrationTag.Alerting]: 'Alerting',
  [IntegrationTag.BiTools]: 'BI tools',
  [IntegrationTag.ComponentReady]: 'Component-ready',
  [IntegrationTag.Compute]: 'Compute',
  [IntegrationTag.EltTools]: 'ELT tools',
  [IntegrationTag.Metadata]: 'Metadata',
  [IntegrationTag.Monitoring]: 'Monitoring',
  [IntegrationTag.Notifications]: 'Notifications',
  [IntegrationTag.Storage]: 'Storage',
};

export const IntegrationTagIcon: Record<IntegrationTag, IconName> = {
  [IntegrationTag.Alerting]: 'alert',
  [IntegrationTag.BiTools]: 'chart_bar',
  [IntegrationTag.ComponentReady]: 'repo',
  [IntegrationTag.Compute]: 'speed',
  [IntegrationTag.EltTools]: 'transform',
  [IntegrationTag.Metadata]: 'metadata',
  [IntegrationTag.Monitoring]: 'visibility',
  [IntegrationTag.Notifications]: 'notifications',
  [IntegrationTag.Storage]: 'download',
};
