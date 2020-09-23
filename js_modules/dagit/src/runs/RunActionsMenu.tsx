import {
  Button,
  Intent,
  Menu,
  MenuDivider,
  MenuItem,
  Popover,
  Position,
  Tooltip,
} from '@blueprintjs/core';
import gql from 'graphql-tag';
import * as qs from 'query-string';
import * as React from 'react';
import {useLazyQuery, useMutation} from 'react-apollo';

import {showCustomAlert} from '../CustomAlertProvider';
import {DagsterRepositoryContext} from '../DagsterRepositoryContext';
import {SharedToaster} from '../DomUtils';
import {ROOT_SERVER_URI} from '../DomUtils';
import {HighlightedCodeBlock} from '../HighlightedCodeBlock';

import {REEXECUTE_PIPELINE_UNKNOWN} from './RunActionButtons';
import {
  CANCEL_MUTATION,
  DELETE_MUTATION,
  LAUNCH_PIPELINE_REEXECUTION_MUTATION,
  RunsQueryRefetchContext,
  getReexecutionVariables,
  handleLaunchResult,
} from './RunUtils';
import {RunActionMenuFragment} from './types/RunActionMenuFragment';
import {RunTableRunFragment} from './types/RunTableRunFragment';

export const RunActionsMenu: React.FunctionComponent<{
  run: RunTableRunFragment | RunActionMenuFragment;
}> = React.memo(({run}) => {
  const {refetch} = React.useContext(RunsQueryRefetchContext);

  const [reexecute] = useMutation(LAUNCH_PIPELINE_REEXECUTION_MUTATION);
  const [cancel] = useMutation(CANCEL_MUTATION, {onCompleted: refetch});
  const [destroy] = useMutation(DELETE_MUTATION, {onCompleted: refetch});
  const [loadEnv, {called, loading, data}] = useLazyQuery(PipelineEnvironmentYamlQuery, {
    variables: {runId: run.runId},
  });

  const repoContext = React.useContext(DagsterRepositoryContext);
  const repositoryLocation = repoContext?.repositoryLocation;
  const repository = repoContext?.repository;

  const envYaml = data?.pipelineRunOrError?.runConfigYaml;
  const infoReady = called ? !loading : false;
  return (
    <Popover
      content={
        <Menu>
          <MenuItem
            text={loading ? 'Loading Configuration...' : 'View Configuration...'}
            disabled={envYaml == null}
            icon="share"
            onClick={() =>
              showCustomAlert({
                title: 'Config',
                body: <HighlightedCodeBlock value={envYaml} languages={['yaml']} />,
              })
            }
          />
          <MenuDivider />
          {repository ? (
            <>
              <Tooltip
                content={OPEN_PLAYGROUND_UNKNOWN}
                position={Position.BOTTOM}
                disabled={infoReady}
                wrapperTagName="div"
              >
                <MenuItem
                  text="Open in Playground..."
                  disabled={!infoReady}
                  icon="edit"
                  target="_blank"
                  href={`/pipeline/${run.pipelineName}/playground/setup?${qs.stringify({
                    mode: run.mode,
                    config: envYaml,
                    solidSelection: run.solidSelection,
                  })}`}
                />
              </Tooltip>
              <Tooltip
                content={REEXECUTE_PIPELINE_UNKNOWN}
                position={Position.BOTTOM}
                disabled={infoReady}
                wrapperTagName="div"
              >
                <MenuItem
                  text="Re-execute"
                  disabled={!infoReady}
                  icon="repeat"
                  onClick={async () => {
                    const result = await reexecute({
                      variables: getReexecutionVariables({
                        run,
                        envYaml,
                        repositoryLocationName: repositoryLocation?.name || '',
                        repositoryName: repository?.name,
                      }),
                    });
                    handleLaunchResult(run.pipelineName, result, {openInNewWindow: false});
                  }}
                />
              </Tooltip>
              <MenuItem
                text="Cancel"
                icon="stop"
                disabled={!run.canTerminate}
                onClick={async () => {
                  const result = await cancel({variables: {runId: run.runId}});
                  showToastFor(
                    result.data.terminatePipelineExecution,
                    `Run ${run.runId} cancelled.`,
                  );
                }}
              />
              <MenuDivider />
            </>
          ) : null}
          <MenuItem
            text="Download Debug File"
            icon="download"
            download
            href={`${ROOT_SERVER_URI}/download_debug/${run.runId}`}
          />
          <MenuItem
            text="Delete"
            icon="trash"
            disabled={run.canTerminate}
            onClick={async () => {
              const result = await destroy({variables: {runId: run.runId}});
              showToastFor(result.data.deletePipelineRun, `Run ${run.runId} deleted.`);
            }}
          />
        </Menu>
      }
      position={'bottom'}
      onOpening={() => {
        if (!called) {
          loadEnv();
        }
      }}
    >
      <Button minimal={true} icon="more" />
    </Popover>
  );
});

export const RunBulkActionsMenu: React.FunctionComponent<{
  selected: RunTableRunFragment[];
  onChangeSelection: (runs: RunTableRunFragment[]) => void;
}> = React.memo(({selected, onChangeSelection}) => {
  const {refetch} = React.useContext(RunsQueryRefetchContext);
  const [cancel] = useMutation(CANCEL_MUTATION, {onCompleted: refetch});
  const [destroy] = useMutation(DELETE_MUTATION, {onCompleted: refetch});

  const cancelable = selected.filter((r) => r.canTerminate);
  const deletable = selected.filter((r) => !r.canTerminate);

  return (
    <Popover
      content={
        <Menu>
          <MenuItem
            icon="stop"
            text={`Cancel ${cancelable.length} ${cancelable.length === 1 ? 'run' : 'runs'}`}
            disabled={cancelable.length === 0}
            onClick={async () => {
              for (const run of cancelable) {
                const result = await cancel({variables: {runId: run.runId}});
                showToastFor(result.data.terminatePipelineExecution, `Run ${run.runId} cancelled.`);
              }
              onChangeSelection([]);
            }}
          />
          <MenuItem
            icon="trash"
            text={`Delete ${deletable.length} ${deletable.length === 1 ? 'run' : 'runs'}`}
            disabled={deletable.length === 0}
            onClick={async () => {
              for (const run of deletable) {
                const result = await destroy({variables: {runId: run.runId}});
                showToastFor(result.data.deletePipelineRun, `Run ${run.runId} deleted.`);
              }
              // we could remove just the runs that are deleted and leave the others, but we may
              // need to test it for a while and see what seems natural.
              onChangeSelection([]);
            }}
          />
        </Menu>
      }
      position={'bottom'}
    >
      <Button disabled={selected.length === 0} text="Actions" rightIcon="caret-down" small />
    </Popover>
  );
});

const OPEN_PLAYGROUND_UNKNOWN =
  'Playground is unavailable because the pipeline is not present in the current repository.';

function showToastFor(
  possibleError: {__typename: string; message?: string},
  successMessage: string,
) {
  if ('message' in possibleError) {
    SharedToaster.show({
      message: possibleError.message,
      icon: 'error',
      intent: Intent.DANGER,
    });
  } else {
    SharedToaster.show({
      message: successMessage,
      icon: 'confirm',
      intent: Intent.SUCCESS,
    });
  }
}

// Avoid fetching envYaml on load in Runs page. It is slow.
const PipelineEnvironmentYamlQuery = gql`
  query PipelineEnvironmentYamlQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      ... on PipelineRun {
        runConfigYaml
      }
    }
  }
`;
