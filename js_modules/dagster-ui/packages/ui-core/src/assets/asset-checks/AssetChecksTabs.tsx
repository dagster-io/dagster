import {Tab, Tabs, Tooltip} from '@dagster-io/ui-components';

export type AssetChecksTabType = 'overview' | 'execution-history' | 'automation-history';

interface Props {
  activeTab: AssetChecksTabType;
  enableAutomationHistory: boolean;
  onChange: (tabId: AssetChecksTabType) => void;
}

export const AssetChecksTabs = ({activeTab, enableAutomationHistory, onChange}: Props) => {
  return (
    <Tabs selectedTabId={activeTab} onChange={onChange}>
      <Tab id="overview" title="概览" />
      <Tab id="execution-history" title="执行历史" />
      <Tab
        id="automation-history"
        title={
          <Tooltip
            content="此资产检查未配置自动化条件。"
            canShow={!enableAutomationHistory}
            placement="top"
          >
            自动化历史
          </Tooltip>
        }
        disabled={!enableAutomationHistory}
      />
    </Tabs>
  );
};
