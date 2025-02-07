import {Box, Tab, Tabs, Tag} from '@dagster-io/ui-components';

import {useFeatureFlags} from '../app/Flags';

export type ConcurrencyTab = 'run-concurrency' | 'key-concurrency';

interface Props {
  activeTab: ConcurrencyTab;
  onChange: (tab: ConcurrencyTab) => void;
}

export const ConcurrencyTabs = ({activeTab, onChange}: Props) => {
  const {flagPoolUI} = useFeatureFlags();
  return (
    <Tabs selectedTabId={activeTab} onChange={onChange}>
      <Tab
        title="Run concurrency"
        id="run-concurrency"
        selected={activeTab === 'run-concurrency'}
      />
      <Tab
        title={
          <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
            <span>{flagPoolUI ? 'Pools' : 'Global op/asset concurrency'}</span>
            <Tag>
              <span style={{fontWeight: 'normal'}}>Experimental</span>
            </Tag>
          </Box>
        }
        id="key-concurrency"
        selected={activeTab === 'key-concurrency'}
      />
    </Tabs>
  );
};
