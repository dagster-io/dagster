import {Tab, Tabs} from '@dagster-io/ui-components';
import qs from 'qs';

import {AssetViewParams} from './types';
import {AssetViewDefinitionNodeFragment} from './types/AssetView.types';
import {TabLink} from '../ui/TabLink';
import {FeatureFlag, featureEnabled} from '../app/Flags';

interface Props {
  selectedTab: string;
  tabs: AssetTabConfig[];
}

export const AssetTabs = (props: Props) => {
  const {selectedTab, tabs} = props;

  return (
    <Tabs size="large" selectedTabId={selectedTab}>
      {tabs
        .filter((tab) => !tab.hidden)
        .map(({id, title, to, disabled}) => {
          if (disabled) {
            return <Tab disabled key={id} id={id} title={title} />;
          }
          return <TabLink key={id} id={id} title={title} to={to} disabled={disabled} />;
        })}
    </Tabs>
  );
};

export const DEFAULT_ASSET_TAB_ORDER = featureEnabled(FeatureFlag.flagUseNewAssetOverviewPage)
  ? ['overview', 'executions', 'automation', 'checks', 'insights', 'plots', 'lineage', 'partitions']
  : ['partitions', 'events', 'checks', 'plots', 'definition', 'lineage', 'automation'];

export type AssetTabConfigInput = {
  definition: AssetViewDefinitionNodeFragment | null;
  params: AssetViewParams;
};

export type AssetTabConfig = {
  id: string;
  title: string;
  to: string;
  disabled?: boolean;
  hidden?: boolean;
};

export const buildAssetViewParams = (params: AssetViewParams) => `?${qs.stringify(params)}`;

export const buildAssetTabMap = (input: AssetTabConfigInput): Record<string, AssetTabConfig> => {
  const {definition, params} = input;
  const experimental = featureEnabled(FeatureFlag.flagUseNewAssetOverviewPage);

  return {
    partitions: {
      id: 'partitions',
      title: 'Partitions',
      to: buildAssetViewParams({...params, view: 'partitions'}),
      hidden: !definition?.partitionDefinition || definition?.isSource,
    },
    checks: {
      id: 'checks',
      title: 'Checks',
      to: buildAssetViewParams({...params, view: 'checks'}),
      hidden: !definition?.hasAssetChecks && !experimental,
    },
    events: {
      id: 'events',
      title: experimental ? 'Executions' : 'Events',
      to: buildAssetViewParams({...params, view: 'events', partition: undefined}),
    },
    overview: {
      id: 'overview',
      title: 'Overview',
      to: buildAssetViewParams({...params, view: 'overview'}),
      disabled: !definition,
    },
    plots: {
      id: 'plots',
      title: experimental ? 'Insights' : 'Plots',
      to: buildAssetViewParams({...params, view: 'plots'}),
    },
    definition: {
      id: 'definition',
      title: 'Definition',
      to: buildAssetViewParams({...params, view: 'definition'}),
      disabled: !definition,
    },
    lineage: {
      id: 'lineage',
      title: 'Lineage',
      to: buildAssetViewParams({...params, view: 'lineage'}),
      disabled: !definition,
    },
    automation: {
      id: 'automation',
      title: 'Automation',
      to: buildAssetViewParams({...params, view: 'automation'}),
      disabled: !definition,
      hidden: !definition?.autoMaterializePolicy,
    },
  };
};

export const buildAssetTabs = (input: AssetTabConfigInput): AssetTabConfig[] => {
  const tabConfigs = buildAssetTabMap(input);

  return DEFAULT_ASSET_TAB_ORDER.map((tabId) => tabConfigs[tabId]).filter(
    (tab): tab is AssetTabConfig => !!tab && !tab.hidden,
  );
};
