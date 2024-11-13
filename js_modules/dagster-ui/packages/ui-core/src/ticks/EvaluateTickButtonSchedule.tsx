import {Box, Button} from '@dagster-io/ui-components';
import {useState} from 'react';

import {EvaluateScheduleDialog} from './EvaluateScheduleDialog';
import {RepoAddress} from '../workspace/types';

interface EvaluateTickButtonScheduleProps {
  name: string;
  repoAddress: RepoAddress;
  jobName: string;
}

export const EvaluateTickButtonSchedule = ({
  name,
  repoAddress,
  jobName,
}: EvaluateTickButtonScheduleProps) => {
  const [showTestTickDialog, setShowTestTickDialog] = useState(false);

  return (
    <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
      <Button
        onClick={() => {
          setShowTestTickDialog(true);
        }}
      >
        Evaluate tick
      </Button>
      <EvaluateScheduleDialog
        key={showTestTickDialog ? '1' : '0'} // change key to reset dialog state
        isOpen={showTestTickDialog}
        onClose={() => {
          setShowTestTickDialog(false);
        }}
        name={name}
        repoAddress={repoAddress}
        jobName={jobName}
      />
    </Box>
  );
};
