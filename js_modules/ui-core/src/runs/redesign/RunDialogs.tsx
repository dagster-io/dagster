import {CreateIssueForRunDialog} from '@shared/runs/CreateIssueForRunDialog';
import {RunMetricsDialog} from '@shared/runs/RunMetricsDialog';
import {useContext} from 'react';

import {RunTagsDialog} from './RunTagsDialog';
import {MappedRun} from './mapRunsFeedData';
import {DeletionDialog} from '../DeletionDialog';
import {QueuedRunCriteriaDialog} from '../QueuedRunCriteriaDialog';
import {RunConfigDialog} from '../RunConfigDialog';
import {RunsQueryRefetchContext} from '../RunUtils';
import {TerminationDialog} from '../TerminationDialog';

export type RunDialog =
  | {kind: 'create-issue'; run: MappedRun}
  | {kind: 'queue-criteria'; run: MappedRun}
  | {kind: 'metrics'; run: MappedRun}
  | {kind: 'tags'; run: MappedRun}
  | {kind: 'config'; run: MappedRun; runConfigYaml: string; isJob: boolean}
  | {kind: 'terminate'; run: MappedRun}
  | {kind: 'delete'; run: MappedRun};

type RunDialogsProps = {
  dialog: RunDialog;
  onOpenDialog: (dialog: RunDialog) => void;
  onClose: () => void;
};

export const RunDialogs = ({dialog, onOpenDialog, onClose}: RunDialogsProps) => {
  const {run} = dialog;
  const {refetch} = useContext(RunsQueryRefetchContext);

  switch (dialog.kind) {
    case 'create-issue':
      return <CreateIssueForRunDialog runId={run.id} isOpen onClose={onClose} />;
    case 'queue-criteria':
      return <QueuedRunCriteriaDialog run={run} isOpen onClose={onClose} />;
    case 'metrics':
      return RunMetricsDialog ? <RunMetricsDialog runId={run.id} isOpen onClose={onClose} /> : null;
    case 'tags':
      return <RunTagsDialog run={run} onClose={onClose} />;
    case 'config':
      return (
        <RunConfigDialog
          isOpen
          onClose={onClose}
          runConfigYaml={dialog.runConfigYaml}
          mode={run.mode}
          isJob={dialog.isJob}
        />
      );
    case 'terminate':
      return (
        <TerminationDialog
          isOpen
          onClose={onClose}
          onComplete={refetch}
          selectedRuns={{[run.id]: run.canTerminate}}
        />
      );
    case 'delete':
      return (
        <DeletionDialog
          isOpen
          onClose={onClose}
          onComplete={refetch}
          onTerminateInstead={() => onOpenDialog({kind: 'terminate', run})}
          selectedRuns={{[run.id]: run.canTerminate && run.hasTerminatePermission}}
        />
      );
  }
};
