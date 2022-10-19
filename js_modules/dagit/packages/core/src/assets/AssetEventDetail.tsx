import {Box, Colors, Heading} from '@dagster-io/ui';
import React from 'react';

import {AssetEventGroup} from './groupByPartition';

export const AssetEventDetail: React.FC<{group: AssetEventGroup}> = ({group}) => {
  return (
    <Box padding={{horizontal: 24}} background={Colors.Gray10} style={{flex: 1}}>
      <Box
        padding={{vertical: 24}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        flex={{alignItems: 'center', justifyContent: 'space-between'}}
      >
        <Heading>{group.partition}</Heading>
      </Box>
      <Box
        style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr'}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        padding={{vertical: 16}}
      >
        <Box>
          <div style={{fontWeight: 600}}>Event</div>
        </Box>
        <Box>
          <div style={{fontWeight: 600}}>Partition</div>
        </Box>
        <Box>
          <div style={{fontWeight: 600}}>Run</div>
        </Box>
        <Box>
          <div style={{fontWeight: 600}}>Job</div>
        </Box>
      </Box>
      <Box padding={{top: 24}}>
        <div style={{fontWeight: 600}}>Expectations</div>
      </Box>
      <Box padding={{top: 24}}>
        <div style={{fontWeight: 600}}>Metadata</div>
      </Box>
    </Box>
  );
};

export const AssetEventDetailEmpty = () => <Box />;
