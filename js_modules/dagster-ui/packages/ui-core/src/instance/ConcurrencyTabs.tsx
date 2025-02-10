import {Tab, Tabs} from '@dagster-io/ui-components';

export type ConcurrencyTab = 'run-concurrency' | 'key-concurrency';

interface Props {
  activeTab: ConcurrencyTab;
  onChange: (tab: ConcurrencyTab) => void;
}

export const ConcurrencyTabs = ({activeTab, onChange}: Props) => {
  return (
    <Tabs selectedTabId={activeTab} onChange={onChange}>
      <Tab
        title="Run concurrency"
        id="run-concurrency"
        selected={activeTab === 'run-concurrency'}
      />
      <Tab title="Pools" id="key-concurrency" selected={activeTab === 'key-concurrency'} />
    </Tabs>
  );
};
