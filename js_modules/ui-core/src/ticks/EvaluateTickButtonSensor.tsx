import {Box, Button, Icon, Tooltip} from '@dagster-io/ui-components';
import {useState} from 'react';

import {SensorDryRunDialog} from './SensorDryRunDialog';
import {SensorType} from '../graphql/types';
import {RepoAddress} from '../workspace/types';

interface EvaluateTickButtonSensorProps {
  cursor: string;
  name: string;
  repoAddress: RepoAddress;
  jobName: string;
  sensorType: SensorType;
}

export const EvaluateTickButtonSensor = ({
  cursor,
  name,
  repoAddress,
  jobName,
  sensorType,
}: EvaluateTickButtonSensorProps) => {
  const [showTestTickDialog, setShowTestTickDialog] = useState(false);

  return (
    <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
      <Tooltip
        canShow={sensorType !== SensorType.STANDARD}
        content="Testing not available for this sensor type"
        placement="top-end"
      >
        <Button
          disabled={sensorType !== SensorType.STANDARD}
          onClick={() => setShowTestTickDialog(true)}
          icon={<Icon name="preview_tick" />}
        >
          Preview tick result
        </Button>
      </Tooltip>
      <SensorDryRunDialog
        isOpen={showTestTickDialog}
        onClose={() => setShowTestTickDialog(false)}
        currentCursor={cursor}
        name={name}
        repoAddress={repoAddress}
        jobName={jobName}
      />
    </Box>
  );
};
