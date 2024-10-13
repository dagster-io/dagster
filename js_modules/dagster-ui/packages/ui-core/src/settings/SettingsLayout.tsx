import {Box, Heading, PageHeader} from '@dagster-io/ui-components';

import {ReloadAllButton} from '../workspace/ReloadAllButton';

interface Props {
  left: React.ReactNode;
  main: React.ReactNode;
}

export const SettingsLayout = ({left, main}: Props) => {
  return (
    <Box style={{height: '100%', overflow: 'hidden'}} flex={{direction: 'column'}}>
      <PageHeader
        title={<Heading>Deployment</Heading>}
        right={<ReloadAllButton label="Reload definitions" />}
      />
      <Box style={{overflow: 'hidden'}} flex={{direction: 'row', grow: 1}}>
        <Box style={{flex: '0 0 292px', overflowY: 'auto'}} border="right">
          {left}
        </Box>
        <Box
          flex={{direction: 'column', alignItems: 'stretch'}}
          style={{flex: 1, overflow: 'hidden'}}
        >
          {main}
        </Box>
      </Box>
    </Box>
  );
};
