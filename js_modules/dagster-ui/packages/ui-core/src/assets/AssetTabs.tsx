import {Tab, Tabs} from '@dagster-io/ui-components';
import qs from 'qs';

import {AssetViewParams} from './types';
import {AssetViewDefinitionNodeFragment} from './types/AssetView.types';
import {TabLink} from '../ui/TabLink';

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

export const DEFAULT_ASSET_TAB_ORDER = [
  'overview',
  'launchpad',
  'executions',
  'automation',
  'checks',
  'insights',
  'plots',
  'lineage',
  'partitions',
];

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
    },
    executions: {
      id: 'executions',
      title: 'Executions',
      to: buildAssetViewParams({...params, view: 'executions', partition: undefined}),
    },
    overview: {
      id: 'overview',
      title: 'Overview',
      to: buildAssetViewParams({...params, view: 'overview'}),
      disabled: !definition,
    },
    plots: {
      id: 'plots',
      title: 'Insights',
      to: buildAssetViewParams({...params, view: 'plots'}),
    },
    automation: {
      id: 'automation',
      title: 'Automation',
      to: buildAssetViewParams({...params, view: 'automation'}),
      disabled: !definition,
      hidden: !definition?.autoMaterializePolicy,
    },
    launchpad: {
      id: 'launchpad',
      title: 'Launchpad',
      to: buildAssetViewParams({...params, view: 'launchpad'}),
      disabled: !definition,
    },
  };
};

export const buildAssetTabs = (input: AssetTabConfigInput): AssetTabConfig[] => {
  const tabConfigs = buildAssetTabMap(input);
  return DEFAULT_ASSET_TAB_ORDER.map((tabId) => tabConfigs[tabId]).filter(
    (tab): tab is AssetTabConfig => !!tab && !tab.hidden,
  );
};
