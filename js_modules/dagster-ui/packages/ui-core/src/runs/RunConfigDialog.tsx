import {useMutation} from '@apollo/client';
import {
  Box,
  Button,
  Dialog,
  DialogFooter,
  Group,
  Icon,
  Menu,
  MenuItem,
  Popover,
  StyledRawCodeMirror,
  Subheading,
  Tooltip,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components';

import {AppContext} from '../app/AppContext';
import {showSharedToaster} from '../app/DomUtils';
import {useCopyToClipboard} from '../app/browser';
import {FREE_CONCURRENCY_SLOTS_MUTATION} from '../instance/InstanceConcurrency';
import {
  FreeConcurrencySlotsMutation,
  FreeConcurrencySlotsMutationVariables,
} from '../instance/types/InstanceConcurrency.types';
import {NO_LAUNCH_PERMISSION_MESSAGE} from '../launchpad/LaunchRootExecutionButton';
import {AnchorButton} from '../ui/AnchorButton';
import {workspacePathFromRunDetails, workspacePipelinePath} from '../workspace/workspacePath';

import {DeletionDialog} from './DeletionDialog';
import {doneStatuses} from './RunStatuses';
import {RunTags} from './RunTags';
import {RunsQueryRefetchContext} from './RunUtils';
import {TerminationDialog} from './TerminationDialog';
import {RunFragment} from './types/RunFragments.types';

type VisibleDialog = 'config' | 'delete' | 'terminate' | 'free_slots' | null;

export const RunConfigDialog = ({run, isJob}: {run: RunFragment; isJob: boolean}) => {
  const {runConfigYaml} = run;
  const [visibleDialog, setVisibleDialog] = React.useState<VisibleDialog>(null);

  const {rootServerURI} = React.useContext(AppContext);
  const {refetch} = React.useContext(RunsQueryRefetchContext);

  const copy = useCopyToClipboard();
  const history = useHistory();

  const [freeSlots] = useMutation<
    FreeConcurrencySlotsMutation,
    FreeConcurrencySlotsMutationVariables
  >(FREE_CONCURRENCY_SLOTS_MUTATION);

  const copyConfig = async () => {
    copy(runConfigYaml);
    await showSharedToaster({
      intent: 'success',
      icon: 'copy_to_clipboard_done',
      message: 'Copied!',
    });
  };

  const freeConcurrencySlots = async () => {
    const resp = await freeSlots({variables: {runId: run.id}});
    if (resp.data?.freeConcurrencySlots) {
      await showSharedToaster({
        intent: 'success',
        icon: 'check_circle',
        message: 'Freed concurrency slots',
      });
    }
  };

  const jobPath = workspacePathFromRunDetails({
    id: run.id,
    repositoryName: run.repositoryOrigin?.repositoryName,
    repositoryLocationName: run.repositoryOrigin?.repositoryLocationName,
    pipelineName: run.pipelineName,
    isJob,
  });

  return (
    <div>
      <Group direction="row" spacing={8}>
        {run.hasReExecutePermission ? (
          <AnchorButton icon={<Icon name="edit" />} to={jobPath}>
            Open in Launchpad
          </AnchorButton>
        ) : (
          <Tooltip content={NO_LAUNCH_PERMISSION_MESSAGE} useDisabledButtonTooltipFix>
            <Button icon={<Icon name="edit" />} disabled>
              Open in Launchpad
            </Button>
          </Tooltip>
        )}
        <Button icon={<Icon name="tag" />} onClick={() => setVisibleDialog('config')}>
          View tags and config
        </Button>
        <Popover
          position="bottom-right"
          content={
            <Menu>
              <Tooltip
                content="Loadable in dagster-webserver-debug"
                position="left"
                targetTagName="div"
              >
                <MenuItem
                  text="Download debug file"
                  icon={<Icon name="download_for_offline" />}
                  onClick={() => window.open(`${rootServerURI}/download_debug/${run.id}`)}
                />
              </Tooltip>
              {run.hasConcurrencyKeySlots && doneStatuses.has(run.status) ? (
                <MenuItem
                  text="Free concurrency slots"
                  icon={<Icon name="lock" />}
                  onClick={freeConcurrencySlots}
                />
              ) : null}
              {run.hasDeletePermission ? (
                <MenuItem
                  icon="delete"
                  text="Delete"
                  intent="danger"
                  onClick={() => setVisibleDialog('delete')}
                />
              ) : null}
            </Menu>
          }
        >
          <Button icon={<Icon name="expand_more" />} />
        </Popover>
      </Group>
      <Dialog
        isOpen={visibleDialog === 'config'}
        onClose={() => setVisibleDialog(null)}
        style={{
          width: '90vw',
          maxWidth: '1000px',
          minWidth: '600px',
          height: '90vh',
          maxHeight: '1000px',
          minHeight: '600px',
        }}
        title="Run configuration"
      >
        <Box flex={{direction: 'column'}} style={{flex: 1, overflow: 'hidden'}}>
          <Box flex={{direction: 'column', gap: 20}} style={{flex: 1, overflow: 'hidden'}}>
            <Box flex={{direction: 'column', gap: 12}} padding={{top: 16, horizontal: 24}}>
              <Subheading>Tags</Subheading>
              <div>
                <RunTags tags={run.tags} mode={isJob ? null : run.mode} />
              </div>
            </Box>
            <Box flex={{direction: 'column'}} style={{flex: 1, overflow: 'hidden'}}>
              <Box border="bottom" padding={{left: 24, bottom: 16}}>
                <Subheading>Config</Subheading>
              </Box>
              <CodeMirrorContainer>
                <StyledRawCodeMirror
                  value={runConfigYaml}
                  options={{readOnly: true, lineNumbers: true, mode: 'yaml'}}
                  theme={['config-editor']}
                />
              </CodeMirrorContainer>
            </Box>
          </Box>
          <DialogFooter topBorder>
            <Button onClick={() => copyConfig()} intent="none">
              Copy config
            </Button>
            <Button onClick={() => setVisibleDialog(null)} intent="primary">
              OK
            </Button>
          </DialogFooter>
        </Box>
      </Dialog>
      {run.hasDeletePermission ? (
        <DeletionDialog
          isOpen={visibleDialog === 'delete'}
          onClose={() => setVisibleDialog(null)}
          onComplete={() => {
            if (run.repositoryOrigin) {
              history.push(
                workspacePipelinePath({
                  repoName: run.repositoryOrigin.repositoryName,
                  repoLocation: run.repositoryOrigin.repositoryLocationName,
                  pipelineName: run.pipelineName,
                  isJob,
                  path: '/runs',
                }),
              );
            } else {
              setVisibleDialog(null);
            }
          }}
          onTerminateInstead={() => setVisibleDialog('terminate')}
          selectedRuns={{[run.id]: run.canTerminate}}
        />
      ) : null}
      {run.hasTerminatePermission ? (
        <TerminationDialog
          isOpen={visibleDialog === 'terminate'}
          onClose={() => setVisibleDialog(null)}
          onComplete={() => {
            refetch();
          }}
          selectedRuns={{[run.id]: run.canTerminate}}
        />
      ) : null}
    </div>
  );
};

const CodeMirrorContainer = styled.div`
  flex: 1;
  overflow: hidden;

  .CodeMirror {
    height: 100%;
  }
`;
