import {gql, useQuery} from '@apollo/client';
import qs from 'query-string';
import * as React from 'react';
import styled from 'styled-components/macro';

import {AppContext} from '../app/AppContext';
import {OptionsContainer, OptionsDivider} from '../gantt/VizComponents';
import {useViewport} from '../gantt/useViewport';
import {QueryPersistedStateConfig, useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {PIPELINE_EXPLORER_SOLID_HANDLE_FRAGMENT} from '../pipelines/PipelineExplorer';
import {Box} from '../ui/Box';
import {ButtonWIP} from '../ui/Button';
import {ColorsWIP} from '../ui/Colors';
import {DialogBody, DialogFooter, DialogWIP} from '../ui/Dialog';
import {IconWIP} from '../ui/Icon';
import {MenuItemWIP, MenuWIP} from '../ui/Menu';
import {Popover} from '../ui/Popover';
import {TokenizingFieldValue} from '../ui/TokenizingField';
import {FontFamily} from '../ui/styles';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {PartitionProgress} from './PartitionProgress';
import {PartitionRunListForStep} from './PartitionRunListForStep';
import {
  BOX_SIZE,
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
  DisplayOptions,
  isStepKeyForNode,
  MatrixStep,
  StatusSquareFinalColor,
  useMatrixData,
} from './useMatrixData';

const TITLE_TOTAL_FAILURES = 'This step failed at least once for this percent of partitions.';

const TITLE_FINAL_FAILURES = 'This step failed to run successfully for this percent of partitions.';

const OVERSCROLL = 200;

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

const timeboundsOfPartitions = (partitionColumns: {steps: {unix: number}[]}[]) => {
  let [minUnix, maxUnix] = [Date.now() / 1000, 1];
  for (const partition of partitionColumns) {
    for (const step of partition.steps) {
      if (step.unix === 0) {
        continue;
      }
      [minUnix, maxUnix] = [Math.min(minUnix, step.unix), Math.max(maxUnix, step.unix)];
    }
  }
  return [minUnix, maxUnix] as const;
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
    colorizeSliceUnix: Number(qs.colorizeSliceUnix || 0),
    showFailuresAndGapsOnly: qs.showFailuresAndGapsOnly === 'true',
  }),
  defaults: {
    showPrevious: false,
    colorizeByAge: false,
    showFailuresAndGapsOnly: false,
    colorizeSliceUnix: 0,
  },
};

export const PartitionRunMatrix: React.FC<PartitionRunMatrixProps> = (props) => {
  const {basePath} = React.useContext(AppContext);
  const {viewport, containerProps} = useViewport();
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

  const visibleRangeStart = Math.max(0, Math.floor((viewport.left - OVERSCROLL) / BOX_SIZE));
  const visibleCount = Math.ceil((viewport.width + OVERSCROLL * 2) / BOX_SIZE);
  const visibleColumns = partitionColumns.slice(
    visibleRangeStart,
    visibleRangeStart + visibleCount,
  );
  const [minUnix, maxUnix] = timeboundsOfPartitions(partitionColumns);

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
      <OptionsContainer>
        <strong>Run Matrix</strong>
        <OptionsDivider />
        <RunTagsTokenizingField
          runs={partitions.reduce(
            (a, b) => [...a, ...b.runs],
            [] as {tags: {key: string; value: string}[]}[],
          )}
          onChange={props.setRunTags}
          tokens={props.runTags}
        />
        {props.runTags.length && _backfillIdFromTags(props.runTags) ? (
          <Box flex={{grow: 1}} margin={{left: 12, right: 8}}>
            <PartitionProgress
              pipelineName={props.pipelineName}
              repoAddress={props.repoAddress}
              backfillId={_backfillIdFromTags(props.runTags)}
            />
          </Box>
        ) : null}
        <div style={{flex: 1}} />

        <RunMatrixSettings
          options={options}
          setOptions={setOptions}
          minUnix={minUnix}
          maxUnix={maxUnix}
        />
      </OptionsContainer>
      <div
        style={{
          position: 'relative',
          display: 'flex',
          borderBottom: `1px solid ${ColorsWIP.KeylineGray}`,
        }}
      >
        <GridFloatingContainer floating={viewport.left > 0}>
          <GridColumn disabled style={{flex: 1, flexShrink: 1, overflow: 'hidden'}}>
            <TopLabel></TopLabel>
            <LeftLabel style={{paddingLeft: 24}}>Number of Runs</LeftLabel>
            <Divider />
            {stepRows.map((step) => (
              <LeftLabel
                style={{paddingLeft: 8 + step.x}}
                key={step.name}
                data-tooltip={step.name}
                hovered={step.name === hovered?.stepName}
              >
                {step.name}
              </LeftLabel>
            ))}
          </GridColumn>
          {options.showPrevious && (
            <GridColumn disabled>
              <TopLabel />
              <LeftLabel
                style={{width: 32, textAlign: 'right'}}
                onClick={() =>
                  setStepSort(stepSort === SORT_TOTAL_DESC ? SORT_TOTAL_ASC : SORT_TOTAL_DESC)
                }
              >
                <IconSorter
                  $sorting={[SORT_TOTAL_DESC, SORT_TOTAL_ASC].includes(stepSort)}
                  $asc={stepSort === SORT_TOTAL_ASC}
                />
              </LeftLabel>
              <Divider />
              {stepRows.map(({totalFailurePercent, name}, idx) => (
                <LeftLabel
                  key={idx}
                  title={TITLE_TOTAL_FAILURES}
                  hovered={name === hovered?.stepName}
                >
                  <RedBox
                    $filled={totalFailurePercent > 0}
                    style={{background: `rgba(255, 0, 0, ${(totalFailurePercent / 100) * 0.6})`}}
                  >
                    {`${totalFailurePercent}%`}
                  </RedBox>
                </LeftLabel>
              ))}
              <Divider />
            </GridColumn>
          )}
          <GridColumn disabled>
            <TopLabel />
            <LeftLabel
              style={{width: 42}}
              onClick={() =>
                setStepSort(stepSort === SORT_FINAL_DESC ? SORT_FINAL_ASC : SORT_FINAL_DESC)
              }
            >
              <IconSorter
                $sorting={[SORT_FINAL_DESC, SORT_FINAL_ASC].includes(stepSort)}
                $asc={stepSort === SORT_FINAL_ASC}
              />
            </LeftLabel>
            <Divider />
            {stepRows.map(({finalFailurePercent, name}, idx) => (
              <LeftLabel
                key={idx}
                title={TITLE_FINAL_FAILURES}
                hovered={name === hovered?.stepName}
              >
                <RedBox
                  $filled={finalFailurePercent > 0}
                  style={{
                    background: `rgba(255, 0, 0, ${(finalFailurePercent / 100) * 0.6})`,
                    right: 12,
                  }}
                >
                  {`${finalFailurePercent}%`}
                </RedBox>
              </LeftLabel>
            ))}
          </GridColumn>
        </GridFloatingContainer>
        <GridScrollContainer {...containerProps}>
          <div
            style={{
              width: partitionColumns.length * BOX_SIZE,
              position: 'relative',
              height: '100%',
            }}
          >
            {visibleColumns.map((p, idx) => (
              <GridColumn
                key={p.name}
                style={{
                  zIndex: visibleColumns.length - idx,
                  width: BOX_SIZE,
                  position: 'absolute',
                  left: (idx + visibleRangeStart) * BOX_SIZE,
                }}
              >
                <TopLabelTilted label={p.name} />
                <LeftLabel style={{textAlign: 'center'}}>{p.runs.length}</LeftLabel>
                <Divider />
                {sortPartitionSteps(p.steps).map((s) => (
                  <PartitionStepSquare
                    key={s.name}
                    step={s}
                    runs={p.runs}
                    options={options}
                    minUnix={minUnix}
                    maxUnix={maxUnix}
                    basePath={basePath}
                    hovered={hovered}
                    setHovered={setHovered}
                    setFocused={setFocused}
                    partitionName={p.name}
                  />
                ))}
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
  border-top: 1px solid ${ColorsWIP.KeylineGray};
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

const RunMatrixSettings: React.FC<{
  options: DisplayOptions;
  setOptions: (options: DisplayOptions) => void;
  minUnix: number;
  maxUnix: number;
}> = ({options, setOptions, minUnix, maxUnix}) => {
  return (
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
              <Box flex={{direction: 'column', gap: 8}}>
                <div>Colorize by age</div>
                {options.colorizeByAge ? (
                  <div style={{marginLeft: '9px'}}>
                    <SliceSlider
                      disabled={false}
                      value={Math.max(minUnix, options.colorizeSliceUnix)}
                      onChange={(v) => setOptions({...options, colorizeSliceUnix: v})}
                      maxUnix={maxUnix}
                      minUnix={minUnix}
                    />
                  </div>
                ) : null}
              </Box>
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
      <ButtonWIP icon={<IconWIP name="tune" />}>Settings</ButtonWIP>
    </Popover>
  );
};

const RedBox = styled.div<{$filled: boolean}>`
  position: absolute;
  top: 6px;
  right: 6px;
  font-size: 14px;
  cursor: pointer;
  color: ${(p) => (p.$filled ? ColorsWIP.Red500 : ColorsWIP.Gray300)};
  line-height: 20px;
  padding: ${(p) => (p.$filled ? `0 4px;` : `0`)};
  border-radius: 3px;
  display: inline-block;
  font-family: ${FontFamily.monospace};
`;

const IconSorter: React.FC<{$asc: boolean; $sorting: boolean}> = ({$asc, $sorting}) => (
  <IconWIP
    name="arrow_drop_down"
    size={24}
    style={{
      transform: $asc ? 'rotate(-180deg)' : 'rotate(0deg)',
      opacity: $sorting ? 1 : 0.25,
      marginTop: 4,
      marginLeft: 'auto',
      marginRight: 8,
    }}
  />
);

const PartitionStepSquare: React.FC<{
  step: MatrixStep;
  runs: PartitionRunMatrixRunFragment[];
  options: DisplayOptions;
  basePath: string;
  hovered: PartitionRunSelection | null;
  minUnix: number;
  maxUnix: number;
  partitionName: string;
  setHovered: (hovered: PartitionRunSelection | null) => void;
  setFocused: (hovered: PartitionRunSelection | null) => void;
}> = ({
  step,
  runs,
  options,
  hovered,
  setHovered,
  setFocused,
  minUnix,
  maxUnix,
  basePath,
  partitionName,
}) => {
  const [opened, setOpened] = React.useState(false);
  const {name, color, unix} = step;

  const className = `square
  ${runs.length === 0 && 'empty'}
  ${(options.showPrevious ? color : StatusSquareFinalColor[color] || color).toLowerCase()}`;

  const content = (
    <div
      className={className}
      onMouseEnter={() => setHovered({stepName: name, partitionName})}
      onMouseLeave={() => setHovered(null)}
      style={
        options.colorizeByAge
          ? {
              opacity:
                unix >= options.colorizeSliceUnix
                  ? 0.3 + 0.7 * ((unix - minUnix) / (maxUnix - minUnix))
                  : 0.08,
            }
          : {}
      }
    />
  );

  if (
    !opened &&
    (!runs.length || hovered?.stepName !== name || hovered?.partitionName !== partitionName)
  ) {
    return content;
  }

  const lastRunHref = `${basePath}/instance/runs/${runs[runs.length - 1].runId}?${qs.stringify({
    selection: name,
    logs: `step:${name}`,
  })}`;

  return (
    <Popover
      interactionKind="click"
      placement="bottom-start"
      onOpened={() => setOpened(true)}
      onClosed={() => setOpened(false)}
      content={
        <MenuWIP>
          <MenuItemWIP icon="open_in_new" text="Show Logs From Last Run" href={lastRunHref} />
          <MenuItemWIP
            icon="settings_backup_restore"
            text={`View Runs (${runs.length})`}
            onClick={() => setFocused({stepName: name, partitionName})}
          />
        </MenuWIP>
      }
    >
      {content}
    </Popover>
  );
};
