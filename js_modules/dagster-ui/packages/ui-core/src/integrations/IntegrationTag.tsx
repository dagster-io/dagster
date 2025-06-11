import {Box, Colors, Icon, IconName, Tag} from '@dagster-io/ui-components';

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
  [IntegrationTag.BiTools]: 'BI',
  [IntegrationTag.CommunitySupported]: 'Community Supported',
  [IntegrationTag.Compute]: 'Compute',
  [IntegrationTag.DagsterSupported]: 'Built by Dagster Labs',
  [IntegrationTag.EtlTools]: 'ETL',
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

export const BuiltByDagsterLabs = () => (
  <Box
    flex={{direction: 'row', alignItems: 'center', gap: 4}}
    style={{fontSize: 12, color: Colors.textLight()}}
  >
    <Icon name="shield_check" size={12} color={Colors.textLight()} />
    Built by Dagster Labs
  </Box>
);

export const PrivateIntegration = () => (
  <Box
    flex={{direction: 'row', alignItems: 'center', gap: 4}}
    style={{fontSize: 12, color: Colors.textLight()}}
  >
    <Icon name="lock" size={12} color={Colors.textLight()} />
    Private
  </Box>
);

export const IntegrationTags = ({tags}: {tags: string[]}) => (
  <>
    {tags
      .filter(
        (tag): tag is IntegrationTag =>
          IntegrationTagKeys.includes(tag) && tag !== IntegrationTag.DagsterSupported,
      )
      .map((tag) => (
        <Tag key={tag} icon={IntegrationTagIcon[tag] ?? undefined}>
          {IntegrationTagLabel[tag]}
        </Tag>
      ))}
  </>
);
