import {Box, Button, Icon} from '@dagster-io/ui-components';
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
        icon={<Icon name="preview_tick" />}
        onClick={() => {
          setShowTestTickDialog(true);
        }}
      >
        Preview tick result
      </Button>
      <EvaluateScheduleDialog
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
