import {Tab, Tabs} from '@dagster-io/ui-components';

export type AssetChecksTabType = 'overview' | 'execution-history';

interface Props {
  activeTab: AssetChecksTabType;
  onChange: (tabId: AssetChecksTabType) => void;
}

export const AssetChecksTabs = ({activeTab, onChange}: Props) => {
  return (
    <Tabs selectedTabId={activeTab} onChange={(tabId) => onChange(tabId as AssetChecksTabType)}>
      <Tab id="overview" title="Overview" />
      <Tab id="execution-history" title="Execution history" />
    </Tabs>
  );
};
