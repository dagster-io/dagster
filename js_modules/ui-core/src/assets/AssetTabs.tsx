import {
  Icon,
  Menu,
  MenuItem,
  Popover,
  Tab,
  Tabs,
  Tooltip,
  UnstyledButton,
} from '@dagster-io/ui-components';
import qs from 'qs';
import {useMemo, useState} from 'react';

import styles from './css/AssetTabs.module.css';
import {AssetViewParams} from './types';
import {useIsMobile} from '../app/layout/IsMobileContext';
import {MenuLink} from '../ui/MenuLink';
import {TabLink} from '../ui/TabLink';

interface Props {
  selectedTab: string;
  tabs: AssetTabConfig[];
}

export const AssetTabs = (props: Props) => {
  const {selectedTab, tabs} = props;
  const isMobile = useIsMobile();

  if (isMobile) {
    return <AssetTabPicker selectedTab={selectedTab} tabs={tabs} />;
  }

  return (
    <Tabs size="large" selectedTabId={selectedTab}>
      {tabs
        .filter((tab) => !tab.hidden)
        .map(({id, title, to, tooltip, disabled}) => {
          if (disabled) {
            return (
              <Tab
                disabled
                key={id}
                id={id}
                title={
                  <Tooltip content={tooltip || ''} canShow={!!tooltip} placement="top">
                    {title}
                  </Tooltip>
                }
              />
            );
          }
          return <TabLink key={id} id={id} title={title} to={to} disabled={disabled} />;
        })}
    </Tabs>
  );
};

/**
 * The tab row doesn't fit on a phone, and a horizontally scrolling row hides most of it.
 * The tabs become a full-width control that opens the same list as a menu instead.
 */
const AssetTabPicker = ({selectedTab, tabs}: Props) => {
  const [isOpen, setIsOpen] = useState(false);

  const visibleTabs = tabs.filter((tab) => !tab.hidden);
  if (visibleTabs.length === 0) {
    return null;
  }
  const selected = visibleTabs.find((tab) => tab.id === selectedTab) ?? visibleTabs[0];

  return (
    <Popover
      fill
      matchTargetWidth
      className={styles.pickerTarget}
      placement="bottom-start"
      isOpen={isOpen}
      onInteraction={(nextOpen) => setIsOpen(nextOpen)}
      content={
        <Menu>
          {visibleTabs.map(({id, title, to, tooltip, disabled}) =>
            disabled ? (
              <MenuItem key={id} text={tooltip ? `${title} — ${tooltip}` : title} disabled />
            ) : (
              <MenuLink
                key={id}
                to={to}
                text={title}
                active={id === selectedTab}
                onClick={() => setIsOpen(false)}
              />
            ),
          )}
        </Menu>
      }
    >
      <UnstyledButton
        type="button"
        className={styles.picker}
        aria-haspopup="menu"
        aria-expanded={isOpen}
      >
        <span>{selected?.title}</span>
        <Icon name="arrow_drop_down" />
      </UnstyledButton>
    </Popover>
  );
};

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

export type AssetTabConfig = {
  id: string;
  title: string;
  to: string;
  disabled?: boolean;
  tooltip?: string;
  hidden?: boolean;
};

export const buildAssetViewParams = (params: AssetViewParams) => `?${qs.stringify(params)}`;

export const buildAssetTabMap = (input: AssetTabConfigInput) => {
  const {definition} = input;

  return {
    overview: {
      id: 'overview',
      title: 'Overview',
      to: buildAssetViewParams({view: 'overview'}),
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
