import {Box, PageHeader} from '@dagster-io/ui-components';

import {ReloadAllButton} from '../workspace/ReloadAllButton';

interface Props {
  tabs: React.ReactNode;
  main: React.ReactNode;
}

export const SettingsLayout = ({tabs, main}: Props) => {
  return (
    <Box style={{height: '100%', overflow: 'hidden'}} flex={{direction: 'column'}}>
      <PageHeader right={<ReloadAllButton label="Reload definitions" />} tabs={tabs} />
      <Box style={{overflow: 'hidden'}} flex={{direction: 'row', grow: 1}}>
        {main}
      </Box>
    </Box>
  );
};
