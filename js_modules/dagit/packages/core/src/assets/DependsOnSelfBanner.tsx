import {Alert, Box, Colors, Icon} from '@dagster-io/ui';
import React from 'react';

export const DependsOnSelfBanner: React.FC = () => {
  return (
    <Box
      padding={{vertical: 16, left: 24, right: 12}}
      border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
    >
      <Alert
        intent="info"
        icon={
          <Icon name="history_toggle_off" size={16} color={Colors.Blue700} style={{marginTop: 1}} />
        }
        title={
          <div style={{fontWeight: 400}}>This asset depends on earlier partitions of itself. </div>
        }
      />
    </Box>
  );
};
