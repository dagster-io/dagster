import {Box, Heading, PageHeader} from '@dagster-io/ui-components';

import {useIsMobile} from '../app/layout/IsMobileContext';
import {ReloadAllButton} from '../workspace/ReloadAllButton';

interface Props {
  tabs: React.ReactNode;
  main: React.ReactNode;
}

export const SettingsLayout = ({tabs, main}: Props) => {
  const isMobile = useIsMobile();
  return (
    <Box style={{height: '100%', overflow: 'hidden'}} flex={{direction: 'column'}}>
      <PageHeader
        // On mobile the menu button floats over the first header row, so the tabs need a
        // title row above them.
        title={
          isMobile ? (
            <Heading size={16} weight={600}>
              Deployment
            </Heading>
          ) : undefined
        }
        // `PageHeader` only renders `right` beside a title, so desktop never shows this; match it.
        right={isMobile ? undefined : <ReloadAllButton label="Reload definitions" />}
        tabs={tabs}
      />
      <Box style={{overflow: 'hidden'}} flex={{direction: 'row', grow: 1}}>
        {main}
      </Box>
    </Box>
  );
};
