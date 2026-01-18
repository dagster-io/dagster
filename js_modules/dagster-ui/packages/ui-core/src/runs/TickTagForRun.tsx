import {Box, MiddleTruncate, Tag} from '@dagster-io/ui-components';
import {useState} from 'react';

import {DagsterTag} from './RunTag';
import {InstigationSelector} from '../graphql/types';
import {TickDetailsDialog} from '../instigation/TickDetailsDialog';
import {TickLogDialog} from '../ticks/TickLogDialog';
import {TagActionsPopover} from '../ui/TagActions';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {workspacePathFromAddress} from '../workspace/workspacePath';

interface Props {
  instigationSelector: InstigationSelector;
  instigationType: DagsterTag.SensorName | DagsterTag.ScheduleName;
  tickId: string;
}

export const TickTagForRun = ({instigationSelector, instigationType, tickId}: Props) => {
  const [showDetails, setShowDetails] = useState(false);
  const [showLogs, setShowLogs] = useState(false);
  const icon = instigationType === DagsterTag.ScheduleName ? 'schedule' : 'sensors';
  const {name, repositoryName, repositoryLocationName} = instigationSelector;
  const repoAddress = buildRepoAddress(repositoryName, repositoryLocationName);

  const actions = [
    {
      label: `View ${instigationType === DagsterTag.ScheduleName ? 'schedule' : 'sensor'}`,
      to: workspacePathFromAddress(
        repoAddress,
        `${instigationType === DagsterTag.ScheduleName ? '/schedules' : '/sensors'}/${name}`,
      ),
    },
    {
      label: 'View tick details',
      onClick: () => setShowDetails(true),
    },
    {
      label: 'View tick logs',
      onClick: () => setShowLogs(true),
    },
  ];

  return (
    <>
      <TagActionsPopover actions={actions} data={{key: 'Launched by', value: name}}>
        <Tag icon={icon}>
          <Box flex={{direction: 'row'}}>
            <span>Launched by&nbsp;</span>
            <div style={{maxWidth: '140px'}}>
              <MiddleTruncate text={name} />
            </div>
          </Box>
        </Tag>
      </TagActionsPopover>
      <TickDetailsDialog
        isOpen={showDetails}
        tickResultType="runs"
        onClose={() => setShowDetails(false)}
        instigationSelector={instigationSelector}
        tickId={tickId}
      />
      <TickLogDialog
        isOpen={showLogs}
        onClose={() => setShowLogs(false)}
        instigationSelector={instigationSelector}
        tickId={tickId}
      />
    </>
  );
};
