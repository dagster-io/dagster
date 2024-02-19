import {gql, useMutation, useQuery} from '@apollo/client';
import {
  Box,
  Button,
  Checkbox,
  Colors,
  DialogBody,
  DialogFooter,
  Icon,
  NonIdealState,
  Spinner,
  Subheading,
  Tooltip,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {useHistory} from 'react-router-dom';

import {
  DAEMON_NOT_RUNNING_ALERT_INSTANCE_FRAGMENT,
  DaemonNotRunningAlert,
  USING_DEFAULT_LAUNCHER_ALERT_INSTANCE_FRAGMENT,
  UsingDefaultLauncherAlert,
  showBackfillErrorToast,
  showBackfillSuccessToast,
} from './BackfillMessaging';
import {DimensionRangeWizard} from './DimensionRangeWizard';
import {PartitionRunStatusCheckboxes, countsByState} from './PartitionRunStatusCheckboxes';
import {
  BackfillSelectorQuery,
  BackfillSelectorQueryVariables,
} from './types/BackfillSelector.types';
import {PipelineRunTag} from '../app/ExecutionSessionStorage';
import {filterByQuery} from '../app/GraphQueryImpl';
import {isTimeseriesPartition} from '../assets/MultipartitioningSupport';
import {GanttChartMode} from '../gantt/GanttChart';
import {buildLayout} from '../gantt/GanttChartLayout';
import {PartitionDefinitionType, RunStatus} from '../graphql/types';
import {LAUNCH_PARTITION_BACKFILL_MUTATION} from '../instance/backfill/BackfillUtils';
import {
  LaunchPartitionBackfillMutation,
  LaunchPartitionBackfillMutationVariables,
} from '../instance/backfill/types/BackfillUtils.types';
import {LaunchButton} from '../launchpad/LaunchButton';
import {TagContainer, TagEditor} from '../launchpad/TagEditor';
import {explodeCompositesInHandleGraph} from '../pipelines/CompositeSupport';
import {GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT} from '../pipelines/GraphExplorer';
import {GraphQueryInput} from '../ui/GraphQueryInput';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

interface BackfillOptions {
  reexecute: boolean;
  fromFailure: boolean;
}

export const BackfillPartitionSelector = ({
  partitionSetName,
  onLaunch,
  onCancel,
  onSubmit,
  repoAddress,
  runStatusData,
  pipelineName,
  partitionNames,
}: {
  partitionSetName: string;
  partitionNames: string[];
  runStatusData: {[partitionName: string]: RunStatus};
  pipelineName: string;
  onLaunch?: (backfillId: string, stepQuery: string) => void;
  onCancel?: () => void;
  onSubmit: () => void;
  repoAddress: RepoAddress;
}) => {
  const history = useHistory();
  const [range, _setRange] = React.useState<string[]>(
    Object.keys(runStatusData).filter(
      (k) => !runStatusData[k] || runStatusData[k] === RunStatus.FAILURE,
    ),
  );
  const [stateFilters, setStateFilters] = React.useState<RunStatus[]>([
    RunStatus.NOT_STARTED,
    RunStatus.FAILURE,
  ]);

  const selected = React.useMemo(() => {
    return range.filter((r) => stateFilters.includes(runStatusData[r]!));
  }, [range, stateFilters, runStatusData]);

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
    showBackfillSuccessToast(history, backfillId, false);
    onLaunch?.(backfillId, query);
  };

  const onError = (data: LaunchPartitionBackfillMutation | null | undefined) => {
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

  const isFailed = (name: string) => runStatusData[name] === RunStatus.FAILURE;
  const failedPartitions = partitionNames.filter(isFailed);

  const setRange = (selection: string[]) => {
    const selectionSet = new Set(selection);
    // first order the partition names, according to the order given by partition names, which
    // is the order determined from the partition definition set in user code
    _setRange(partitionNames.filter((name) => selectionSet.has(name)));
    if (options.fromFailure && selection.filter((x) => !isFailed(x)).length > 0) {
      setOptions({...options, fromFailure: false});
    }
  };

  const counts = countsByState(
    range.map((key) => ({
      partitionKey: key,
      state: runStatusData[key]!,
    })),
  );

  return (
    <>
      <DialogBody>
        <Box flex={{direction: 'column', gap: 24}}>
          <Section title="Partitions">
            <Box>
              Select partitions to materialize. Click and drag to select a range on the timeline.
            </Box>

            <DimensionRangeWizard
              selected={range}
              setSelected={setRange}
              health={{runStatusForPartitionKey: (key) => runStatusData[key]}}
              partitionKeys={partitionNames}
              dimensionType={
                isTimeseriesPartition(partitionNames[0])
                  ? PartitionDefinitionType.TIME_WINDOW
                  : PartitionDefinitionType.STATIC
              }
            />

            <PartitionRunStatusCheckboxes
              value={stateFilters}
              onChange={setStateFilters}
              counts={counts}
              allowed={
                options.fromFailure
                  ? [RunStatus.FAILURE]
                  : [
                      RunStatus.NOT_STARTED,
                      RunStatus.FAILURE,
                      RunStatus.QUEUED,
                      RunStatus.STARTED,
                      RunStatus.SUCCESS,
                    ]
              }
            />
          </Section>

          {failedPartitions.length ? (
            <Section title="Reexecution">
              <Checkbox
                checked={options.fromFailure}
                disabled={!selected.every(isFailed)}
                onChange={() => {
                  const next = {
                    ...options,
                    fromFailure: !options.fromFailure,
                    reexecute: !options.reexecute,
                  };

                  if (next.fromFailure) {
                    setStateFilters([RunStatus.FAILURE]);
                  }
                  setQuery('');
                  setOptions(next);
                }}
                label={
                  <Box flex={{display: 'inline-flex', alignItems: 'center'}}>
                    <Box margin={{right: 4}}>Re-execute from failures</Box>
                    <Tooltip
                      placement="top"
                      content="For each partition, if the most recent run failed, launch a re-execution starting from the steps that failed. Only applies for selections of failed partitions."
                    >
                      <Icon name="info" color={Colors.accentGray()} />
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
                  <Icon name="info" color={Colors.accentGray()} />
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
                <div style={{color: Colors.textLight()}}>
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
              <div
                style={{border: `1px solid ${Colors.borderDefault()}`, borderRadius: 8, padding: 3}}
              >
                <TagContainer tagsFromSession={tags} onRequestEdit={() => setTagEditorOpen(true)} />
              </div>
            ) : (
              <div>
                <Button onClick={() => setTagEditorOpen(true)}>Add tags to backfill runs</Button>
              </div>
            )}
          </Section>

          <Box flex={{direction: 'column', gap: 16}}>
            <DaemonNotRunningAlert instance={instance} />

            <UsingDefaultLauncherAlert instance={instance} />
          </Box>
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

const LaunchBackfillButton = ({
  partitionSetName,
  partitionNames,
  reexecutionSteps,
  fromFailure,
  tags,
  onSuccess,
  onError,
  onSubmit,
  repoAddress,
}: {
  partitionSetName: string;
  partitionNames: string[];
  reexecutionSteps?: string[];
  fromFailure?: boolean;
  tags?: PipelineRunTag[];
  onSuccess?: (backfillId: string, isPureAssetBackfill: boolean) => void;
  onError: (data: LaunchPartitionBackfillMutation | null | undefined) => void;
  onSubmit: () => void;
  repoAddress: RepoAddress;
}) => {
  const repositorySelector = repoAddressToSelector(repoAddress);
  const mounted = React.useRef(true);
  const [launchBackfill, {loading}] = useMutation<
    LaunchPartitionBackfillMutation,
    LaunchPartitionBackfillMutationVariables
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
      onSuccess?.(data.launchPartitionBackfill.backfillId, false);
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
          ...GraphExplorerSolidHandleFragment
        }
      }
    }
    instance {
      id
      ...UsingDefaultLauncherAlertInstanceFragment
      ...DaemonNotRunningAlertInstanceFragment
    }
  }

  ${GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT}
  ${DAEMON_NOT_RUNNING_ALERT_INSTANCE_FRAGMENT}
  ${USING_DEFAULT_LAUNCHER_ALERT_INSTANCE_FRAGMENT}
`;

const Section = ({
  title,
  children,
}: {
  title: string | React.ReactNode;
  children: React.ReactNode;
}) => (
  <Box flex={{direction: 'column', gap: 4}}>
    <Subheading>{title}</Subheading>
    <Box flex={{direction: 'column', gap: 8}} padding={{top: 16}} border="top">
      {children}
    </Box>
  </Box>
);
