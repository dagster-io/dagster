import qs from 'qs';
import {useMemo} from 'react';

import {AssetViewParams} from './types';
import {RouteTabConfig, RouteTabs} from '../ui/RouteTabs';

interface Props {
  selectedTab: string;
  tabs: AssetTabConfig[];
}

export const AssetTabs = ({selectedTab, tabs}: Props) => (
  <RouteTabs selectedTabId={selectedTab} tabs={tabs} />
);

export const DEFAULT_ASSET_TAB_ORDER = [
  'overview',
  'partitions',
  'events',
  'checks',
  'lineage',
  'automation',
] as const;

export type AssetTabConfigInput = {
  definition:
    | {
        isMaterializable: boolean;
        isObservable: boolean;
        automationCondition: {__typename: 'AutomationCondition'} | null | undefined;
        partitionDefinition: {__typename: 'PartitionDefinition'} | null | undefined;
      }
    | null
    | undefined;
  params: AssetViewParams;
};

export type AssetTabConfig = RouteTabConfig & {
  title: string;
  tooltip?: string;
};

export const buildAssetViewParams = (params: AssetViewParams) => `?${qs.stringify(params)}`;

export const buildAssetTabMap = (input: AssetTabConfigInput) => {
  const {definition} = input;

  return {
    overview: {
      id: 'overview',
      title: 'Overview',
      to: buildAssetViewParams({view: 'overview'}),
      mobile: true,
    } as AssetTabConfig,
    partitions: {
      id: 'partitions',
      title: 'Partitions',
      to: buildAssetViewParams({view: 'partitions'}),
      hidden: !definition?.partitionDefinition,
    } as AssetTabConfig,
    checks: {
      id: 'checks',
      title: 'Checks',
      to: buildAssetViewParams({view: 'checks'}),
    } as AssetTabConfig,
    events: {
      id: 'events',
      title: 'Events',
      to: buildAssetViewParams({view: 'events', partition: undefined}),
    } as AssetTabConfig,
    lineage: {
      id: 'lineage',
      title: 'Lineage',
      to: buildAssetViewParams({view: 'lineage'}),
      disabled: !definition,
    } as AssetTabConfig,
    automation: {
      id: 'automation',
      title: 'Automation',
      to: buildAssetViewParams({view: 'automation'}),
      disabled: !definition,
      hidden: !definition?.automationCondition,
    } as AssetTabConfig,
  };
};

export const useAssetTabs = (input: AssetTabConfigInput): AssetTabConfig[] => {
  return useMemo(() => {
    const tabConfigs = buildAssetTabMap(input);
    return DEFAULT_ASSET_TAB_ORDER.map((tabId) => tabConfigs[tabId]).filter(
      (tab) => !!tab && !tab.hidden,
    );
  }, [input]);
};
