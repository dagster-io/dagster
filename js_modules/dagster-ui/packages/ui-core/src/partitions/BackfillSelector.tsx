import {
  Body2,
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

import {
  DAEMON_NOT_RUNNING_ALERT_INSTANCE_FRAGMENT,
  DaemonNotRunningAlert,
  USING_DEFAULT_LAUNCHER_ALERT_INSTANCE_FRAGMENT,
  UsingDefaultLauncherAlert,
  isBackfillDaemonHealthy,
  showBackfillErrorToast,
  showBackfillSuccessToast,
} from './BackfillMessaging';
import {DimensionRangeWizard} from './DimensionRangeWizard';
import {PartitionRunStatusCheckboxes, countsByState} from './PartitionRunStatusCheckboxes';
import {gql, useMutation, useQuery} from '../apollo-client';
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
import {tagsWithUIExecutionTags} from '../launchpad/uiExecutionTags';
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
  refreshing,
  pipelineName,
  partitionNames,
}: {
  partitionSetName: string;
  partitionNames: string[];
  runStatusData: {[partitionName: string]: RunStatus};
  refreshing: boolean;
  pipelineName: string;
  onLaunch?: (backfillId: string, stepQuery: string) => void;
  onCancel?: () => void;
  onSubmit: () => void;
  repoAddress: RepoAddress;
}) => {
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
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
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
    showBackfillSuccessToast(backfillId);
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
        <NonIdealState icon="error" title="无法获取作业详情" />
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
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      state: runStatusData[key]!,
    })),
  );

  return (
    <>
      <DialogBody>
        <Box flex={{direction: 'column', gap: 24}}>
          <Section
            title={
              <Box flex={{justifyContent: 'space-between'}}>
                <div>分区</div>
                {refreshing && (
                  <Box flex={{gap: 4, alignItems: 'center'}}>
                    <Spinner purpose="body-text" />
                    <Body2 color={Colors.textLight()}>刷新中...</Body2>
                  </Box>
                )}
              </Box>
            }
          >
            <Box>
              选择要物化的分区。点击并拖拽以在时间线上选择范围。
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
              showQuickSelectOptionsForStatuses={false}
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
            <Section title="重新执行">
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
                    <Box margin={{right: 4}}>从失败处重新执行</Box>
                    <Tooltip
                      placement="top"
                      content="对于每个分区，如果最近一次运行失败，则从失败的步骤开始重新执行。仅适用于选择失败的分区。"
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
                <Box margin={{right: 4}}>步骤子集</Box>
                <Tooltip
                  placement="top"
                  content="为所请求分区的每次运行应用步骤选择。"
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
                placeholder="输入步骤子集"
                onChange={setQuery}
                autoApplyChanges={true}
              />
              {query ? (
                <div style={{color: Colors.textLight()}}>
                  已选择 {stepRows.length} 个步骤
                </div>
              ) : null}
            </Box>
          </Section>

          <Section title="标签">
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
                <Button onClick={() => setTagEditorOpen(true)}>为回填运行添加标签</Button>
              </div>
            )}
          </Section>

          <Box flex={{direction: 'column', gap: 16}}>
            {!isBackfillDaemonHealthy(instance) ? <DaemonNotRunningAlert /> : null}

            <UsingDefaultLauncherAlert instance={instance} />
          </Box>
        </Box>
      </DialogBody>
      <DialogFooter>
        <Button intent="none" onClick={onCancel}>
          取消
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
          tags: tagsWithUIExecutionTags(tags),
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
      return `正在提交 ${count} 个运行…`;
    }

    if (count) {
      return `提交 ${count} 个运行`;
    }

    return '选择要提交的分区';
  };

  const subtitle = () => {
    return !loading && reexecutionCount
      ? `(已选择 ${reexecutionCount} 个步骤)`
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
