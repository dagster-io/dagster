import {Box, Colors} from '@dagster-io/ui-components';

import {StorybookProvider} from '../../testing/StorybookProvider';
import {HelpMenu} from '../HelpMenu';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'HelpMenu',
  component: HelpMenu,
};

export const Default = () => {
  return (
    <StorybookProvider>
      <Box
        background={Colors.navBackground()}
        padding={{horizontal: 48}}
        flex={{alignItems: 'center', justifyContent: 'flex-end'}}
        style={{height: '64px'}}
      >
        <HelpMenu />
      </Box>
    </StorybookProvider>
  );
};
