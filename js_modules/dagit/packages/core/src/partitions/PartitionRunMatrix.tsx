import {gql, useQuery} from '@apollo/client';
import {Colors, Button} from '@blueprintjs/core';
import qs from 'query-string';
import * as React from 'react';
import styled from 'styled-components/macro';

import {AppContext} from '../app/AppContext';
import {useViewport} from '../gantt/useViewport';
import {QueryPersistedStateConfig, useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {PIPELINE_EXPLORER_SOLID_HANDLE_FRAGMENT} from '../pipelines/PipelineExplorer';
import {Box} from '../ui/Box';
import {ButtonWIP} from '../ui/Button';
import {ColorsWIP} from '../ui/Colors';
import {DialogBody, DialogFooter, DialogWIP} from '../ui/Dialog';
import {GraphQueryInput} from '../ui/GraphQueryInput';
import {Group} from '../ui/Group';
import {IconWIP} from '../ui/Icon';
import {MenuItemWIP, MenuWIP} from '../ui/Menu';
import {Popover} from '../ui/Popover';
import {TokenizingFieldValue} from '../ui/TokenizingField';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {PartitionProgress} from './PartitionProgress';
import {PartitionRunListForStep} from './PartitionRunListForStep';
import {
  GridColumn,
  GridFloatingContainer,
  GridScrollContainer,
  LeftLabel,
  TopLabel,
  TopLabelTilted,
} from './RunMatrixUtils';
import {RunTagsTokenizingField} from './RunTagsTokenizingField';
import {SliceSlider} from './SliceSlider';
import {
  PartitionRunMatrixPipelineQuery,
  PartitionRunMatrixPipelineQueryVariables,
} from './types/PartitionRunMatrixPipelineQuery';
import {PartitionRunMatrixRunFragment} from './types/PartitionRunMatrixRunFragment';
import {
  useMatrixData,
  MatrixStep,
  DisplayOptions,
  StatusSquareFinalColor,
  isStepKeyForNode,
} from './useMatrixData';

const TITLE_TOTAL_FAILURES = 'This step failed at least once for this percent of partitions.';

const TITLE_FINAL_FAILURES = 'This step failed to run successfully for this percent of partitions.';

const BOX_COL_WIDTH = 23;

const OVERSCROLL = 150;

const SORT_FINAL_ASC = 'FINAL_ASC';
const SORT_FINAL_DESC = 'FINAL_DESC';
const SORT_TOTAL_ASC = 'TOTAL_ASC';
const SORT_TOTAL_DESC = 'TOTAL_DESC';

interface PartitionRunSelection {
  partitionName: string;
  stepName: string;
}

interface PartitionRunMatrixProps {
  pipelineName: string;
  partitions: {name: string; runs: PartitionRunMatrixRunFragment[]}[];
  repoAddress: RepoAddress;
  runTags: TokenizingFieldValue[];
  setRunTags: (val: TokenizingFieldValue[]) => void;
  stepQuery: string;
  setStepQuery: (val: string) => void;
}

const _backfillIdFromTags = (runTags: TokenizingFieldValue[]) => {
  const [backfillId] = runTags
    .filter((_) => _.token === 'tag' && _.value.startsWith('dagster/backfill='))
    .map((_) => _.value.split('=')[1]);
  return backfillId;
};

const PartitionRunSelectionQueryConfig: QueryPersistedStateConfig<PartitionRunSelection | null> = {
  encode: (val) => ({partitionName: val?.partitionName, stepName: val?.stepName}),
  decode: (qs) =>
    qs.partitionName && qs.stepName
      ? {partitionName: qs.partitionName, stepName: qs.stepName}
      : null,
};

const DisplayOptionsQueryConfig: QueryPersistedStateConfig<DisplayOptions> = {
  decode: (qs) => ({
    showPrevious: qs.showPrevious === 'true',
    colorizeByAge: qs.colorizeByAge === 'true',
    showFailuresAndGapsOnly: qs.showFailuresAndGapsOnly === 'true',
  }),
  defaults: {
    showPrevious: false,
    colorizeByAge: false,
    showFailuresAndGapsOnly: false,
  },
};

export const PartitionRunMatrix: React.FC<PartitionRunMatrixProps> = (props) => {
  const {basePath} = React.useContext(AppContext);
  const {viewport, containerProps} = useViewport();
  const [colorizeSliceUnix, setColorizeSliceUnix] = React.useState(0);
  const [hovered, setHovered] = React.useState<PartitionRunSelection | null>(null);
  const [focused, setFocused] = useQueryPersistedState(PartitionRunSelectionQueryConfig);
  const [stepSort = '', setStepSort] = useQueryPersistedState<string>({queryKey: 'stepSort'});
  const [options, setOptions] = useQueryPersistedState(DisplayOptionsQueryConfig);

  // Retrieve the pipeline's structure
  const repositorySelector = repoAddressToSelector(props.repoAddress);
  const pipelineSelector = {...repositorySelector, pipelineName: props.pipelineName};
  const pipeline = useQuery<
    PartitionRunMatrixPipelineQuery,
    PartitionRunMatrixPipelineQueryVariables
  >(PARTITION_RUN_MATRIX_PIPELINE_QUERY, {
    variables: {pipelineSelector},
  });

  const solidHandles =
    pipeline.data?.pipelineSnapshotOrError.__typename === 'PipelineSnapshot' &&
    pipeline.data.pipelineSnapshotOrError.solidHandles;

  const data = useMatrixData({
    partitions: props.partitions,
    stepQuery: props.stepQuery,
    solidHandles,
    options,
  });

  if (!data || !solidHandles) {
    return <span />;
  }

  const {stepRows, partitionColumns, partitions} = data;
  if (stepSort === SORT_FINAL_ASC) {
    stepRows.sort((a, b) => a.finalFailurePercent - b.finalFailurePercent);
  } else if (stepSort === SORT_FINAL_DESC) {
    stepRows.sort((a, b) => b.finalFailurePercent - a.finalFailurePercent);
  } else if (stepSort === SORT_TOTAL_ASC) {
    stepRows.sort((a, b) => a.totalFailurePercent - b.totalFailurePercent);
  } else if (stepSort === SORT_TOTAL_DESC) {
    stepRows.sort((a, b) => b.totalFailurePercent - a.totalFailurePercent);
  }

  const sortPartitionSteps = (steps: MatrixStep[]) => {
    const stepsByName = {};
    steps.forEach((step) => (stepsByName[step.name] = step));
    return stepRows.map((stepRow) => stepsByName[stepRow.name]);
  };

  const visibleRangeStart = Math.max(0, Math.floor((viewport.left - OVERSCROLL) / BOX_COL_WIDTH));
  const visibleCount = Math.ceil((viewport.width + OVERSCROLL * 2) / BOX_COL_WIDTH);
  const visibleColumns = partitionColumns.slice(
    visibleRangeStart,
    visibleRangeStart + visibleCount,
  );

  let [minUnix, maxUnix] = [Date.now() / 1000, 1];
  for (const partition of partitionColumns) {
    for (const step of partition.steps) {
      if (step.unix === 0) {
        continue;
      }
      [minUnix, maxUnix] = [Math.min(minUnix, step.unix), Math.max(maxUnix, step.unix)];
    }
  }

  return (
    <PartitionRunMatrixContainer>
      <DialogWIP
        isOpen={!!focused}
        onClose={() => setFocused(null)}
        style={{width: '90vw'}}
        title={focused ? `${focused.partitionName} runs (${focused.stepName})` : ''}
      >
        <DialogBody>
          {focused && (
            <PartitionRunListForStep
              pipelineName={props.pipelineName}
              partitionName={focused.partitionName}
              stepName={focused.stepName}
              stepStatsByRunId={Object.assign(
                {},
                ...(props.partitions.find((p) => p.name === focused.partitionName)?.runs || []).map(
                  (run) => ({
                    [run.runId]: run.stepStats.find((s) =>
                      isStepKeyForNode(focused.stepName, s.stepKey),
                    ),
                  }),
                ),
              )}
            />
          )}
        </DialogBody>
        <DialogFooter>
          <ButtonWIP intent="primary" autoFocus={true} onClick={() => setFocused(null)}>
            OK
          </ButtonWIP>
        </DialogFooter>
      </DialogWIP>
      <Box
        flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
        padding={{vertical: 4}}
      >
        <Group direction="row" alignItems="center" spacing={12}>
          <strong>Run Matrix</strong>
          <RunTagsTokenizingField
            runs={partitions.reduce(
              (a, b) => [...a, ...b.runs],
              [] as {tags: {key: string; value: string}[]}[],
            )}
            onChange={props.setRunTags}
            tokens={props.runTags}
          />
        </Group>
        {props.runTags.length && _backfillIdFromTags(props.runTags) ? (
          <Box flex={{grow: 1}} margin={{left: 12, right: 8}}>
            <PartitionProgress
              pipelineName={props.pipelineName}
              repoAddress={props.repoAddress}
              backfillId={_backfillIdFromTags(props.runTags)}
            />
          </Box>
        ) : null}
        <Popover
          position="bottom-left"
          content={
            <MenuWIP>
              <MenuItemWIP
                text="Show previous status"
                icon={
                  <IconWIP
                    name="done"
                    color={options.showPrevious ? ColorsWIP.Gray700 : ColorsWIP.Gray200}
                  />
                }
                onClick={() => setOptions({...options, showPrevious: !options.showPrevious})}
                shouldDismissPopover={false}
              />
              <MenuItemWIP
                text="Only show failures and gaps"
                icon={
                  <IconWIP
                    name="done"
                    color={options.showFailuresAndGapsOnly ? ColorsWIP.Gray700 : ColorsWIP.Gray200}
                  />
                }
                onClick={() =>
                  setOptions({
                    ...options,
                    showFailuresAndGapsOnly: !options.showFailuresAndGapsOnly,
                  })
                }
                shouldDismissPopover={false}
              />
              <MenuItemWIP
                tagName="div"
                text={
                  <Group direction="column" spacing={8}>
                    <div>Colorize by age</div>
                    {options.colorizeByAge ? (
                      <SliceSlider
                        disabled={false}
                        value={Math.max(minUnix, colorizeSliceUnix)}
                        onChange={setColorizeSliceUnix}
                        maxUnix={maxUnix}
                        minUnix={minUnix}
                      />
                    ) : null}
                  </Group>
                }
                icon={
                  <IconWIP
                    name="done"
                    color={options.colorizeByAge ? ColorsWIP.Gray700 : ColorsWIP.Gray200}
                  />
                }
                onClick={() => setOptions({...options, colorizeByAge: !options.colorizeByAge})}
                shouldDismissPopover={false}
              />
            </MenuWIP>
          }
        >
          <Button icon="settings" minimal text="Settings" />
        </Popover>
      </Box>
      <div
        style={{
          position: 'relative',
          display: 'flex',
          border: `1px solid ${Colors.GRAY5}`,
          borderLeft: 0,
        }}
      >
        <GridFloatingContainer floating={viewport.left > 0}>
          <GridColumn disabled style={{flex: 1, flexShrink: 1, overflow: 'hidden'}}>
            <TopLabel>
              <GraphQueryInput
                small
                width={260}
                items={solidHandles.map((h) => h.solid)}
                value={props.stepQuery}
                placeholder="Type a Step Subset"
                onChange={props.setStepQuery}
              />
            </TopLabel>
            {stepRows.map((step) => (
              <LeftLabel
                style={{paddingLeft: step.x}}
                key={step.name}
                data-tooltip={step.name}
                hovered={step.name === hovered?.stepName}
              >
                {step.name}
              </LeftLabel>
            ))}
            <Divider />
            <LeftLabel style={{paddingLeft: 5}}>Runs</LeftLabel>
          </GridColumn>
          {options.showPrevious && (
            <GridColumn disabled>
              <TopLabel>
                <div
                  style={{cursor: 'pointer'}}
                  className="square failure-blank"
                  title={TITLE_TOTAL_FAILURES}
                  onClick={() =>
                    setStepSort(stepSort === SORT_TOTAL_DESC ? SORT_TOTAL_ASC : SORT_TOTAL_DESC)
                  }
                />
              </TopLabel>
              {stepRows.map(({totalFailurePercent, name}, idx) => (
                <LeftLabel
                  key={idx}
                  title={TITLE_TOTAL_FAILURES}
                  hovered={name === hovered?.stepName}
                  redness={totalFailurePercent / 100}
                >
                  {`${totalFailurePercent}%`}
                </LeftLabel>
              ))}
              <Divider />
            </GridColumn>
          )}
          <GridColumn disabled>
            <TopLabel>
              <div
                style={{cursor: 'pointer'}}
                className="square failure"
                title={TITLE_FINAL_FAILURES}
                onClick={() =>
                  setStepSort(stepSort === SORT_FINAL_DESC ? SORT_FINAL_ASC : SORT_FINAL_DESC)
                }
              />
            </TopLabel>
            {stepRows.map(({finalFailurePercent, name}, idx) => (
              <LeftLabel
                key={idx}
                title={TITLE_FINAL_FAILURES}
                hovered={name === hovered?.stepName}
                redness={finalFailurePercent / 100}
              >
                {`${finalFailurePercent}%`}
              </LeftLabel>
            ))}
            <Divider />
          </GridColumn>
        </GridFloatingContainer>
        <GridScrollContainer {...containerProps}>
          <div
            style={{
              width: partitionColumns.length * BOX_COL_WIDTH,
              position: 'relative',
              height: '100%',
            }}
          >
            {visibleColumns.map((p, idx) => (
              <GridColumn
                key={p.name}
                style={{
                  zIndex: visibleColumns.length - idx,
                  width: BOX_COL_WIDTH,
                  position: 'absolute',
                  left: (idx + visibleRangeStart) * BOX_COL_WIDTH,
                }}
                dimSuccesses={!options.colorizeByAge}
              >
                <TopLabelTilted label={p.name} />
                {sortPartitionSteps(p.steps).map(({name, color, unix}) => (
                  <Popover
                    key={name}
                    disabled={p.runs.length === 0}
                    interactionKind="click"
                    placement="bottom-start"
                    content={
                      p.runs.length ? (
                        <MenuWIP>
                          <MenuItemWIP
                            icon="open_in_new"
                            text="Show Logs From Last Run"
                            href={`${basePath}/instance/runs/${
                              p.runs[p.runs.length - 1].runId
                            }?${qs.stringify({
                              selection: name,
                              logs: `step:${name}`,
                            })}`}
                          />
                          <MenuItemWIP
                            icon="settings_backup_restore"
                            text={`View Runs (${p.runs.length})`}
                            onClick={() =>
                              p.runs.length > 0 &&
                              setFocused({stepName: name, partitionName: p.name})
                            }
                          />
                        </MenuWIP>
                      ) : (
                        <span />
                      )
                    }
                  >
                    <div
                      className={`
                      square
                      ${p.runs.length === 0 && 'empty'}
                      ${(options.showPrevious
                        ? color
                        : StatusSquareFinalColor[color] || color
                      ).toLowerCase()}
                    `}
                      onMouseEnter={() => setHovered({stepName: name, partitionName: p.name})}
                      onMouseLeave={() => setHovered(null)}
                      style={
                        options.colorizeByAge
                          ? {
                              opacity:
                                unix >= colorizeSliceUnix
                                  ? 0.3 + 0.7 * ((unix - minUnix) / (maxUnix - minUnix))
                                  : 0.08,
                            }
                          : {}
                      }
                    />
                  </Popover>
                ))}
                <Divider />
                <LeftLabel style={{textAlign: 'center'}}>{p.runs.length}</LeftLabel>
              </GridColumn>
            ))}
          </div>
        </GridScrollContainer>
      </div>
    </PartitionRunMatrixContainer>
  );
};

const PartitionRunMatrixContainer = styled.div`
  display: block;
`;

const Divider = styled.div`
  height: 1px;
  width: 100%;
  margin-top: 5px;
  border-top: 1px solid ${Colors.GRAY5};
`;

export const PARTITION_RUN_MATRIX_RUN_FRAGMENT = gql`
  fragment PartitionRunMatrixRunFragment on PipelineRun {
    id
    runId
    tags {
      key
      value
    }
    stats {
      __typename
      ... on PipelineRunStatsSnapshot {
        id
        startTime
      }
    }
    stepStats {
      __typename
      stepKey
      status
      materializations {
        __typename
      }
      expectationResults {
        success
      }
    }
  }
`;

// add in the explorer fragment, so we can reconstruct the faux-plan steps from the exploded plan
// in the same way we construct the explorer graph
const PARTITION_RUN_MATRIX_PIPELINE_QUERY = gql`
  query PartitionRunMatrixPipelineQuery($pipelineSelector: PipelineSelector) {
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
          ...PipelineExplorerSolidHandleFragment
        }
      }
    }
  }
  ${PIPELINE_EXPLORER_SOLID_HANDLE_FRAGMENT}
`;
