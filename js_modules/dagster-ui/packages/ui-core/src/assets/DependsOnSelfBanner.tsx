import React from 'react';

import {Alert, Box, Icon, colorAccentBlue} from '@dagster-io/ui-components';

export const DependsOnSelfBanner = () => {
  return (
    <Box padding={{vertical: 16, left: 24, right: 12}} border="bottom">
      <Alert
        intent="info"
        icon={
          <Icon
            name="history_toggle_off"
            size={16}
            color={colorAccentBlue()}
            style={{marginTop: 1}}
          />
        }
        title={
          <div style={{fontWeight: 400}}>This asset depends on earlier partitions of itself. </div>
        }
      />
    </Box>
  );
};
