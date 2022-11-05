import {gql, useMutation, useQuery} from '@apollo/client';
import {
  Alert,
  Box,
  Button,
  ButtonLink,
  Checkbox,
  Colors,
  DialogBody,
  DialogFooter,
  Group,
  Icon,
  NonIdealState,
  Spinner,
  Tooltip,
  Mono,
} from '@dagster-io/ui';
import {History} from 'history';
import * as React from 'react';
import {useHistory} from 'react-router';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {SharedToaster} from '../app/DomUtils';
import {PipelineRunTag} from '../app/ExecutionSessionStorage';
import {filterByQuery} from '../app/GraphQueryImpl';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {GanttChartMode} from '../gantt/GanttChart';
import {buildLayout} from '../gantt/GanttChartLayout';
import {LAUNCH_PARTITION_BACKFILL_MUTATION} from '../instance/BackfillUtils';
import {
  LaunchPartitionBackfill,
  LaunchPartitionBackfillVariables,
} from '../instance/types/LaunchPartitionBackfill';
import {LaunchButton} from '../launchpad/LaunchButton';
import {TagEditor, TagContainer} from '../launchpad/TagEditor';
import {explodeCompositesInHandleGraph} from '../pipelines/CompositeSupport';
import {GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT} from '../pipelines/GraphExplorer';
import {GraphQueryInput} from '../ui/GraphQueryInput';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {PartitionRangeWizard} from './PartitionRangeWizard';
import {PartitionState} from './PartitionStatus';
import {BackfillSelectorQuery, BackfillSelectorQueryVariables} from './types/BackfillSelectorQuery';

const DEFAULT_RUN_LAUNCHER_NAME = 'DefaultRunLauncher';

interface BackfillOptions {
  reexecute: boolean;
  fromFailure: boolean;
}

export const BackfillPartitionSelector: React.FC<{
  partitionSetName: string;
  partitionNames: string[];
  partitionData: {[name: string]: PartitionState};
  pipelineName: string;
  onLaunch?: (backfillId: string, stepQuery: string) => void;
  onCancel?: () => void;
  onSubmit: () => void;
  repoAddress: RepoAddress;
}> = ({
  partitionSetName,
  onLaunch,
  onCancel,
  onSubmit,
  repoAddress,
  partitionData,
  pipelineName,
  partitionNames,
}) => {
  const history = useHistory();
  const [selected, _setSelected] = React.useState<string[]>(
    Object.keys(partitionData).filter(
      (k) => !partitionData[k] || partitionData[k] === PartitionState.FAILURE,
    ),
  );
  const [tagEditorOpen, setTagEditorOpen] = React.useState<boolean>(false);
  const [tags, setTags] = React.useState<PipelineRunTag[]>([]);
  const [query, setQuery] = React.useState<string>('');
  const [options, setOptions] = React.useState<BackfillOptions>({
    reexecute: false,
    fromFailure: false,
  });
  const repositorySelector = repoAddressToSelector(repoAddress);

  const {data} = useQuery<BackfillSelectorQuery, BackfillSelectorQueryVariables>(
    BACKFILL_SELECTOR_QUERY,
    {
      variables: {
        pipelineSelector: {
          ...repositorySelector,
          pipelineName,
        },
      },
      fetchPolicy: 'network-only',
    },
  );

  const mounted = React.useRef(true);
  React.useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, [onLaunch]);

  const onSuccess = (backfillId: string) => {
    showBackfillSuccessToast(history, backfillId);
    onLaunch?.(backfillId, query);
  };

  const onError = (data: LaunchPartitionBackfill | null | undefined) => {
    showBackfillErrorToast(data);
  };

  if (!data) {
    return (
      <Box margin={{vertical: 32}} flex={{justifyContent: 'center'}}>
        <Spinner purpose="section" />
      </Box>
    );
  }

  if (data.pipelineSnapshotOrError.__typename !== 'PipelineSnapshot') {
    return (
      <Box margin={20}>
        <NonIdealState icon="error" title="Could not fetch job details" />
      </Box>
    );
  }

  const {pipelineSnapshotOrError: pipelineSnapshot, instance} = data;
  const solids = explodeCompositesInHandleGraph(pipelineSnapshot.solidHandles).map(
    (h: any) => h.solid,
  );
  const solidsFiltered = filterByQuery(solids, query);
  const layout = buildLayout({nodes: solidsFiltered.all, mode: GanttChartMode.FLAT});
  const stepRows = layout.boxes.map((box) => ({
    x: box.x,
    name: box.node.name,
  }));

  const usingDefaultRunLauncher = instance.runLauncher?.name === DEFAULT_RUN_LAUNCHER_NAME;

  const isFailed = (name: string) => partitionData[name] === PartitionState.FAILURE;
  const failedPartitions = partitionNames.filter(isFailed);

  const setSelected = (selection: string[]) => {
    const selectionSet = new Set(selection);
    // first order the partition names, according to the order given by partition names, which
    // is the order determined from the partition definition set in user code
    _setSelected(partitionNames.filter((name) => selectionSet.has(name)));
    if (options.fromFailure && selection.filter((x) => !isFailed(x)).length > 0) {
      setOptions({...options, fromFailure: false});
    }
  };

  return (
    <>
      <DialogBody>
        <Box flex={{direction: 'column', gap: 32}}>
          <Section title="Partitions">
            <PartitionRangeWizard
              selected={selected}
              setSelected={setSelected}
              all={partitionNames}
              partitionData={partitionData}
            />
          </Section>

          {failedPartitions.length ? (
            <Section title="Reexecution">
              <Checkbox
                checked={options.fromFailure}
                disabled={!selected.every(isFailed)}
                onChange={() => {
                  if (!options.fromFailure) {
                    setSelected(failedPartitions);
                  }
                  setQuery('');
                  setOptions({
                    ...options,
                    reexecute: !options.reexecute,
                    fromFailure: !options.fromFailure,
                  });
                }}
                label={
                  <Box flex={{display: 'inline-flex', alignItems: 'center'}}>
                    <Box margin={{right: 4}}>Re-execute from failures</Box>
                    <Tooltip
                      placement="top"
                      content="For each partition, if the most recent run failed, launch a re-execution starting from the steps that failed. Only applies for selections of failed partitions."
                    >
                      <Icon name="info" color={Colors.Gray500} />
                    </Tooltip>
                  </Box>
                }
              />
            </Section>
          ) : null}

          <Section
            title={
              <Box flex={{display: 'inline-flex', alignItems: 'center'}}>
                <Box margin={{right: 4}}>Step subset</Box>
                <Tooltip
                  placement="top"
                  content="Applies a step-selection to each run for the requested partitions."
                >
                  <Icon name="info" color={Colors.Gray500} />
                </Tooltip>
              </Box>
            }
          >
            <Box flex={{direction: 'row', alignItems: 'center', gap: 12}}>
              <GraphQueryInput
                disabled={options.fromFailure}
                width={520}
                items={solids}
                value={query}
                placeholder="Type a step subset"
                onChange={setQuery}
                autoApplyChanges={true}
              />
              {query ? (
                <div style={{color: Colors.Gray500}}>
                  {stepRows.length} step{stepRows.length === 1 ? '' : 's'} selected
                </div>
              ) : null}
            </Box>
          </Section>

          <Section title="Tags">
            <TagEditor
              tagsFromSession={tags}
              onChange={setTags}
              open={tagEditorOpen}
              onRequestClose={() => setTagEditorOpen(false)}
            />
            {tags.length ? (
              <div style={{border: `1px solid ${Colors.Gray300}`, borderRadius: 8, padding: 3}}>
                <TagContainer tagsFromSession={tags} onRequestEdit={() => setTagEditorOpen(true)} />
              </div>
            ) : (
              <div>
                <Button onClick={() => setTagEditorOpen(true)}>Add tags to backfill runs</Button>
              </div>
            )}
          </Section>

          {!instance.daemonHealth.daemonStatus.healthy ? <DaemonNotRunningAlert /> : null}

          {usingDefaultRunLauncher && !instance.runQueuingSupported ? (
            <UsingDefaultLauncherAlert />
          ) : null}
        </Box>
      </DialogBody>
      <DialogFooter>
        <Button intent="none" onClick={onCancel}>
          Cancel
        </Button>
        <LaunchBackfillButton
          partitionNames={selected}
          partitionSetName={partitionSetName}
          reexecutionSteps={
            !options.fromFailure && solidsFiltered.all.length < solids.length
              ? stepRows.map((step) => step.name)
              : undefined
          }
          fromFailure={options.fromFailure}
          tags={tags}
          onSubmit={onSubmit}
          onSuccess={onSuccess}
          onError={onError}
          repoAddress={repoAddress}
        />
      </DialogFooter>
    </>
  );
};

const LaunchBackfillButton: React.FC<{
  partitionSetName: string;
  partitionNames: string[];
  reexecutionSteps?: string[];
  fromFailure?: boolean;
  tags?: PipelineRunTag[];
  onSuccess?: (backfillId: string) => void;
  onError: (data: LaunchPartitionBackfill | null | undefined) => void;
  onSubmit: () => void;
  repoAddress: RepoAddress;
}> = ({
  partitionSetName,
  partitionNames,
  reexecutionSteps,
  fromFailure,
  tags,
  onSuccess,
  onError,
  onSubmit,
  repoAddress,
}) => {
  const repositorySelector = repoAddressToSelector(repoAddress);
  const mounted = React.useRef(true);
  const [launchBackfill, {loading}] = useMutation<
    LaunchPartitionBackfill,
    LaunchPartitionBackfillVariables
  >(LAUNCH_PARTITION_BACKFILL_MUTATION);

  React.useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, [onSuccess]);

  const onLaunch = async () => {
    onSubmit();
    const {data} = await launchBackfill({
      variables: {
        backfillParams: {
          selector: {
            partitionSetName,
            repositorySelector,
          },
          partitionNames,
          reexecutionSteps,
          fromFailure,
          tags,
        },
      },
    });

    if (!mounted.current) {
      return;
    }

    if (data && data.launchPartitionBackfill.__typename === 'LaunchBackfillSuccess') {
      onSuccess?.(data.launchPartitionBackfill.backfillId);
    } else {
      onError?.(data);
    }
  };

  const count = partitionNames.length;
  const reexecutionCount = reexecutionSteps?.length;

  const title = () => {
    if (loading) {
      return `Submitting ${count} ${count === 1 ? 'run' : 'runs'}…`;
    }

    if (count) {
      return `Submit ${count} ${count === 1 ? 'run' : 'runs'}`;
    }

    return 'Select partitions to submit';
  };

  const subtitle = () => {
    return !loading && reexecutionCount
      ? `(${reexecutionCount} selected ${reexecutionCount === 1 ? 'step' : 'steps'})`
      : '';
  };

  const buttonTitle = [title(), subtitle()].join(' ');

  return (
    <LaunchButton
      runCount={count}
      config={{
        title: buttonTitle,
        icon: 'open_in_new',
        disabled: !count || loading,
        onClick: onLaunch,
      }}
    />
  );
};

const BACKFILL_SELECTOR_QUERY = gql`
  query BackfillSelectorQuery($pipelineSelector: PipelineSelector!) {
    pipelineSnapshotOrError(activePipelineSelector: $pipelineSelector) {
      ... on PipelineSnapshot {
        id
        name
        solidHandles {
          handleID
          ...GraphExplorerSolidHandleFragment
          solid {
            name
            definition {
              name
            }
            inputs {
              dependsOn {
                solid {
                  name
                }
              }
            }
            outputs {
              dependedBy {
                solid {
                  name
                }
              }
            }
          }
        }
      }
    }
    instance {
      runLauncher {
        name
      }
      daemonHealth {
        id
        daemonStatus(daemonType: "BACKFILL") {
          id
          healthy
        }
      }
      runQueuingSupported
    }
  }
  ${GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT}
`;

function messageForLaunchBackfillError(data: LaunchPartitionBackfill | null | undefined) {
  const result = data?.launchPartitionBackfill;

  let errors = <></>;
  if (result?.__typename === 'PythonError' || result?.__typename === 'PartitionSetNotFoundError') {
    errors = <PythonErrorInfo error={result} />;
  } else if (result?.__typename === 'InvalidStepError') {
    errors = <div>{`Invalid step: ${result.invalidStepKey}`}</div>;
  } else if (result?.__typename === 'InvalidOutputError') {
    errors = <div>{`Invalid output: ${result.invalidOutputName} for ${result.stepKey}`}</div>;
  } else if (result && 'errors' in result) {
    errors = (
      <>
        {result['errors'].map((error, idx) => (
          <PythonErrorInfo error={error} key={idx} />
        ))}
      </>
    );
  }

  return (
    <Group direction="column" spacing={4}>
      <div>An unexpected error occurred. This backfill was not launched.</div>
      {errors ? (
        <ButtonLink
          color={Colors.White}
          underline="always"
          onClick={() => {
            showCustomAlert({
              body: errors,
            });
          }}
        >
          View error
        </ButtonLink>
      ) : null}
    </Group>
  );
}

export function showBackfillErrorToast(data: LaunchPartitionBackfill | null | undefined) {
  SharedToaster.show({
    message: messageForLaunchBackfillError(data),
    icon: 'error',
    intent: 'danger',
  });
}

export function showBackfillSuccessToast(history: History<unknown>, backfillId: string) {
  SharedToaster.show({
    intent: 'success',
    message: (
      <div>
        Created backfill <Mono>{backfillId}</Mono>
      </div>
    ),
    action: {
      text: 'View',
      onClick: () => history.push(`/instance/backfills`),
    },
  });
}

const DaemonNotRunningAlert: React.FC = () => (
  <Alert
    intent="warning"
    title="The backfill daemon is not running."
    description={
      <div>
        See the{' '}
        <a
          href="https://docs.dagster.io/deployment/dagster-daemon"
          target="_blank"
          rel="noreferrer"
        >
          dagster-daemon documentation
        </a>{' '}
        for more information on how to deploy the dagster-daemon process.
      </div>
    }
  />
);

const UsingDefaultLauncherAlert: React.FC = () => (
  <Alert
    intent="warning"
    title={
      <div>
        Using the default run launcher <code>{DEFAULT_RUN_LAUNCHER_NAME}</code> for launching
        backfills without a queued run coordinator is not advised.
      </div>
    }
    description={
      <div>
        Check your instance configuration in <code>dagster.yaml</code> to either configure the{' '}
        <a
          href="https://docs.dagster.io/deployment/run-coordinator"
          target="_blank"
          rel="noreferrer"
        >
          queued run coordinator
        </a>{' '}
        or to configure a run launcher more appropriate for launching a large number of jobs.
      </div>
    }
  />
);

const Section = ({
  title,
  children,
}: {
  title: string | React.ReactNode;
  children: React.ReactNode;
}) => (
  <Box flex={{direction: 'column', gap: 8}}>
    <strong style={{display: 'block'}}>{title}</strong>
    <Box
      flex={{direction: 'column', gap: 8}}
      padding={{top: 16}}
      border={{width: 1, color: Colors.KeylineGray, side: 'top'}}
    >
      {children}
    </Box>
  </Box>
);
