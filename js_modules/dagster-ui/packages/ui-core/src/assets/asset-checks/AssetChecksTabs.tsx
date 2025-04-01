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
      <Tab id="overview" title="Overview" />
      <Tab id="execution-history" title="Execution history" />
      <Tab
        id="automation-history"
        title={
          <Tooltip
            content="This asset check does not have an automation condition configured."
            canShow={!enableAutomationHistory}
            placement="top"
          >
            Automation history
          </Tooltip>
        }
        disabled={!enableAutomationHistory}
      />
    </Tabs>
  );
};
