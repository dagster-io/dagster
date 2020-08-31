import * as React from "react";
import { uniq } from "lodash";
import { Colors, Checkbox, MultiSlider, Intent } from "@blueprintjs/core";
import styled from "styled-components/macro";

import {
  PartitionRunMatrixPipelineQuery,
  PartitionRunMatrixPipelineQueryVariables,
  PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles
} from "./types/PartitionRunMatrixPipelineQuery";
import { PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results } from "./types/PartitionLongitudinalQuery";
import gql from "graphql-tag";
import { useQuery } from "react-apollo";
import { useRepositorySelector } from "../DagsterRepositoryContext";
import { buildLayout } from "../gaant/GaantChartLayout";
import { GaantChartMode } from "../gaant/GaantChart";
import { formatStepKey } from "../Util";
import { Timestamp } from "../TimeComponents";
import { StepEventStatus } from "../types/globalTypes";
import { GaantChartLayout } from "../gaant/Constants";
import { GraphQueryInput } from "../GraphQueryInput";
import { OptionsDivider } from "../VizComponents";
import { RunTable } from "../runs/RunTable";
import { filterByQuery } from "../GraphQueryImpl";
import {
  tokenizedValuesFromString,
  TokenizingFieldValue,
  stringFromValue,
  TokenizingField
} from "../TokenizingField";
import { shallowCompareKeys } from "@blueprintjs/core/lib/cjs/common/utils";
import { useViewport } from "../gaant/useViewport";
import {
  GridColumn,
  GridFloatingContainer,
  GridScrollContainer,
  LeftLabel,
  TopLabel,
  TopLabelTilted
} from "./RunMatrixUtils";

type Partition = PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results;
type SolidHandle = PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles;

const TITLE_TOTAL_FAILURES = "This step failed at least once for this percent of partitions.";

const TITLE_FINAL_FAILURES = "This step failed to run successfully for this percent of partitions.";

const BOX_COL_WIDTH = 23;

const OVERSCROLL = 150;

function getStartTime(a: Partition["runs"][0]) {
  return ("startTime" in a.stats && a.stats.startTime) || 0;
}
function byStartTimeAsc(a: Partition["runs"][0], b: Partition["runs"][0]) {
  return getStartTime(a) - getStartTime(b);
}

type StatusSquareColor =
  | "SUCCESS"
  | "FAILURE"
  | "FAILURE-SUCCESS"
  | "SKIPPED"
  | "SKIPPED-SUCCESS"
  | "MISSING"
  | "MISSING-SUCCESS";

const StatusSquareFinalColor: { [key: string]: StatusSquareColor } = {
  "FAILURE-SUCCESS": "SUCCESS",
  "SKIPPED-SUCCESS": "SUCCESS",
  "MISSING-SUCCESS": "SUCCESS"
};

interface DisplayOptions {
  showSucessful: boolean;
  showPrevious: boolean;
  colorizeByAge: boolean;
}

interface MatrixStep {
  name: string;
  color: string;
  unix: number;
}

function buildMatrixData(
  layout: GaantChartLayout,
  partitions: Partition[],
  options: DisplayOptions
) {
  // Note this is sorting partition runs in place, I don't think it matters and
  // seems better than cloning all the arrays.
  partitions.forEach(p => p.runs.sort(byStartTimeAsc));

  const partitionColumns = partitions.map(p => ({
    name: p.name,
    runs: p.runs,
    steps: layout.boxes.map(({ node }) => {
      const statuses = p.runs.map(
        r => r.stepStats.find(stats => formatStepKey(stats.stepKey) === node.name)?.status
      );

      // If there was a successful run, calculate age relative to that run since it's the age of materializations.
      // If there are no sucessful runs, the age of the (red) box is just the last run time.
      const lastSuccessIdx = statuses.lastIndexOf(StepEventStatus.SUCCESS);
      const unix =
        lastSuccessIdx !== -1
          ? getStartTime(p.runs[lastSuccessIdx])
          : p.runs.length
          ? getStartTime(p.runs[p.runs.length - 1])
          : 0;

      // Calculate the box color for this step. CSS classes are in the "previous-final" format, and we'll
      // strip the "previous" half later if the user has that display option disabled.
      //
      // Note that the color selection is nuanced because we boil the whole series of statuses into just
      // two colors to display on the box:
      // - For [success, failure], we show success - failures after successful completion are ignored.
      // - For [skipped, failure, success], FAILURE-SUCCESS is more relevant to display than SKIPPED-SUCCESS
      // - For [skipped, failure, skipped], FAILURE is more relevant than SKIPPED.

      let color: StatusSquareColor = statuses[0] || "MISSING";

      if (statuses.length > 1 && lastSuccessIdx !== -1) {
        const prev = statuses.slice(0, lastSuccessIdx);
        color = prev.includes(StepEventStatus.FAILURE)
          ? "FAILURE-SUCCESS"
          : prev.includes(StepEventStatus.SKIPPED)
          ? "SKIPPED-SUCCESS"
          : prev.includes(undefined)
          ? "MISSING-SUCCESS"
          : "SUCCESS";
      } else if (statuses.length > 1) {
        color = statuses.includes(StepEventStatus.FAILURE) ? "FAILURE" : color;
      }

      return {
        name: node.name,
        color,
        unix
      };
    })
  }));

  const stepRows = layout.boxes.map((box, idx) => {
    const totalFailures = partitionColumns.filter(p => p.steps[idx].color.includes("FAILURE"));
    const finalFailures = partitionColumns.filter(p => p.steps[idx].color.endsWith("FAILURE"));
    return {
      x: box.x,
      name: box.node.name,
      totalFailurePercent: Math.round((totalFailures.length / partitionColumns.length) * 100),
      finalFailurePercent: Math.round((finalFailures.length / partitionColumns.length) * 100)
    };
  });

  if (!options.showSucessful) {
    for (let ii = stepRows.length - 1; ii >= 0; ii--) {
      if (stepRows[ii].finalFailurePercent === 0) {
        stepRows.splice(ii, 1);
        partitionColumns.forEach(p => p.steps.splice(ii, 1));
      }
    }
  }

  return { stepRows, partitions, partitionColumns };
}

interface PartitionRunMatrixProps {
  pipelineName: string;
  partitions: Partition[];
  runTags?: { [key: string]: string };
}

interface MatrixDataInputs {
  solidHandles: SolidHandle[] | false;
  partitions: Partition[];
  stepQuery: string;
  runsFilter: TokenizingFieldValue[];
  options: DisplayOptions;
}

/**
 * This hook uses the inputs provided to filter the data displayed and calls through to buildMatrixData.
 * It uses a React ref to cache the result and avoids re-computing when all inputs are shallow-equal.
 *
 * - This could alternatively be implemented via React.memo and an outer + inner component pair, but I
 *   didn't want to split <PartitionRunMatrix />
 * - This can't be a React useEffect with an array of deps because we want the cached value to be updated
 *   synchronously when the inputs are modified to avoid a double-render caused by an effect + state var.
 *
 * @param inputs
 */
const useMatrixData = (inputs: MatrixDataInputs) => {
  const cachedMatrixData = React.useRef<{
    result: ReturnType<typeof buildMatrixData>;
    inputs: MatrixDataInputs;
  }>();
  if (!inputs.solidHandles) {
    return null;
  }
  if (cachedMatrixData.current && shallowCompareKeys(inputs, cachedMatrixData.current.inputs)) {
    return cachedMatrixData.current.result;
  }

  // Filter the runs down to the subset matching the tags input (eg: backfillId)
  const partitionsFiltered = inputs.partitions.map(p => ({
    ...p,
    runs: runsMatchingTagTokens(p.runs, inputs.runsFilter)
  }));

  // Filter the pipeline's structure and build the flat gaant layout for the left hand side
  const solidsFiltered = filterByQuery(
    inputs.solidHandles.map(h => h.solid),
    inputs.stepQuery
  );
  const layout = buildLayout({ nodes: solidsFiltered.all, mode: GaantChartMode.FLAT });

  // Build the matrix of step + partition squares - presorted to match the gaant layout
  const result = buildMatrixData(layout, partitionsFiltered, inputs.options);
  cachedMatrixData.current = { result, inputs };
  return result;
};

const tagsToTokenFieldValues = (runTags?: { [key: string]: string }) => {
  if (!runTags) {
    return [];
  }
  return Object.keys(runTags).map(key => ({ token: "tag", value: `${key}=${runTags[key]}` }));
};

const SORT_FINAL_ASC = "FINAL_ASC";
const SORT_FINAL_DESC = "FINAL_DESC";
const SORT_TOTAL_ASC = "TOTAL_ASC";
const SORT_TOTAL_DESC = "TOTAL_DESC";

export const PartitionRunMatrix: React.FunctionComponent<PartitionRunMatrixProps> = props => {
  const { viewport, containerProps } = useViewport();
  const [runsFilter, setRunsFilter] = React.useState<TokenizingFieldValue[]>(
    tagsToTokenFieldValues(props.runTags)
  );
  const [focusedPartitionName, setFocusedPartitionName] = React.useState<string>("");
  const [hoveredStepName, setHoveredStepName] = React.useState<string>("");
  const [stepQuery, setStepQuery] = React.useState<string>("");
  const [colorizeSliceUnix, setColorizeSliceUnix] = React.useState(0);
  const [stepSortOrder, setSortBy] = React.useState<string>("");
  const [options, setOptions] = React.useState<DisplayOptions>({
    showPrevious: false,
    showSucessful: true,
    colorizeByAge: false
  });
  React.useEffect(() => {
    setRunsFilter(tagsToTokenFieldValues(props.runTags));
  }, [props.runTags]);

  // Retrieve the pipeline's structure
  const repositorySelector = useRepositorySelector();
  const pipelineSelector = { ...repositorySelector, pipelineName: props.pipelineName };
  const pipeline = useQuery<
    PartitionRunMatrixPipelineQuery,
    PartitionRunMatrixPipelineQueryVariables
  >(PARTITION_RUN_MATRIX_PIPELINE_QUERY, {
    variables: { pipelineSelector }
  });

  const solidHandles =
    pipeline.data?.pipelineSnapshotOrError.__typename === "PipelineSnapshot" &&
    pipeline.data.pipelineSnapshotOrError.solidHandles;

  const data = useMatrixData({
    partitions: props.partitions,
    solidHandles,
    stepQuery,
    runsFilter,
    options
  });
  if (!data || !solidHandles) {
    return <span />;
  }

  const { stepRows, partitionColumns, partitions } = data;
  if (stepSortOrder === SORT_FINAL_ASC) {
    stepRows.sort((a, b) => a.finalFailurePercent - b.finalFailurePercent);
  } else if (stepSortOrder === SORT_FINAL_DESC) {
    stepRows.sort((a, b) => b.finalFailurePercent - a.finalFailurePercent);
  } else if (stepSortOrder === SORT_TOTAL_ASC) {
    stepRows.sort((a, b) => a.totalFailurePercent - b.totalFailurePercent);
  } else if (stepSortOrder === SORT_TOTAL_DESC) {
    stepRows.sort((a, b) => b.totalFailurePercent - a.totalFailurePercent);
  }

  const sortPartitionSteps = (steps: MatrixStep[]) => {
    const stepsByName = {};
    steps.forEach(step => (stepsByName[step.name] = step));
    return stepRows.map(stepRow => stepsByName[stepRow.name]);
  };

  const focusedPartition = partitions.find(p => p.name === focusedPartitionName);

  const visibleRangeStart = Math.max(0, Math.floor((viewport.left - OVERSCROLL) / BOX_COL_WIDTH));
  const visibleCount = Math.ceil((viewport.width + OVERSCROLL * 2) / BOX_COL_WIDTH);
  const visibleColumns = partitionColumns.slice(
    visibleRangeStart,
    visibleRangeStart + visibleCount
  );

  let [minUnix, maxUnix] = [Date.now() / 1000, 1];
  for (const partition of partitionColumns) {
    for (const step of partition.steps) {
      if (step.unix === 0) continue;
      [minUnix, maxUnix] = [Math.min(minUnix, step.unix), Math.max(maxUnix, step.unix)];
    }
  }

  return (
    <PartitionRunMatrixContainer>
      <OptionsContainer>
        <strong>Partition Run Matrix</strong>
        <div style={{ width: 20 }} />
        <Checkbox
          label="Show Previous Run States"
          checked={options.showPrevious}
          onChange={() => setOptions({ ...options, showPrevious: !options.showPrevious })}
          style={{ marginBottom: 0, height: 20 }}
        />
        <OptionsDivider />
        <Checkbox
          label="Show Successful Steps"
          checked={options.showSucessful}
          onChange={() => setOptions({ ...options, showSucessful: !options.showSucessful })}
          style={{ marginBottom: 0, height: 20 }}
        />
        <OptionsDivider />
        <Checkbox
          label="Colorize by Age"
          checked={options.colorizeByAge}
          onChange={() => setOptions({ ...options, colorizeByAge: !options.colorizeByAge })}
          style={{ marginBottom: 0, height: 20 }}
        />
        <div style={{ width: 20 }} />
        <SliceSlider
          disabled={!options.colorizeByAge}
          value={Math.max(minUnix, colorizeSliceUnix)}
          onChange={setColorizeSliceUnix}
          maxUnix={maxUnix}
          minUnix={minUnix}
        />
        <div style={{ flex: 1 }} />
        <RunTagsTokenizingField
          runs={partitions.reduce((a, b) => [...a, ...b.runs], [])}
          onChange={setRunsFilter}
          tokens={runsFilter}
        />
      </OptionsContainer>
      <div
        style={{
          position: "relative",
          display: "flex",
          border: `1px solid ${Colors.GRAY5}`,
          borderLeft: 0
        }}
      >
        <GridFloatingContainer floating={viewport.left > 0}>
          <GridColumn disabled style={{ flexShrink: 1, overflow: "hidden" }}>
            <TopLabel>
              <GraphQueryInput
                small
                width={260}
                items={solidHandles.map(h => h.solid)}
                value={stepQuery}
                placeholder="Type a Step Subset"
                onChange={setStepQuery}
              />
            </TopLabel>
            {stepRows.map(step => (
              <LeftLabel
                style={{ paddingLeft: step.x }}
                key={step.name}
                data-tooltip={step.name}
                hovered={step.name === hoveredStepName}
              >
                {step.name}
              </LeftLabel>
            ))}
            <Divider />
            <LeftLabel style={{ paddingLeft: 5 }}>Runs</LeftLabel>
          </GridColumn>
          <GridColumn disabled>
            <TopLabel>
              <div
                style={{ cursor: "pointer" }}
                className="square failure-blank"
                title={TITLE_TOTAL_FAILURES}
                onClick={() =>
                  setSortBy(stepSortOrder === SORT_TOTAL_DESC ? SORT_TOTAL_ASC : SORT_TOTAL_DESC)
                }
              />
            </TopLabel>
            {stepRows.map(({ totalFailurePercent, name }, idx) => (
              <LeftLabel
                key={idx}
                title={TITLE_TOTAL_FAILURES}
                hovered={name === hoveredStepName}
                redness={totalFailurePercent / 100}
              >
                {`${totalFailurePercent}%`}
              </LeftLabel>
            ))}
            <Divider />
          </GridColumn>
          <GridColumn disabled>
            <TopLabel>
              <div
                style={{ cursor: "pointer" }}
                className="square failure"
                title={TITLE_FINAL_FAILURES}
                onClick={() =>
                  setSortBy(stepSortOrder === SORT_FINAL_DESC ? SORT_FINAL_ASC : SORT_FINAL_DESC)
                }
              />
            </TopLabel>
            {stepRows.map(({ finalFailurePercent, name }, idx) => (
              <LeftLabel
                key={idx}
                title={TITLE_FINAL_FAILURES}
                hovered={name === hoveredStepName}
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
              position: "relative",
              height: "100%"
            }}
          >
            {visibleColumns.map((p, idx) => (
              <GridColumn
                key={p.name}
                style={{
                  zIndex: visibleColumns.length - idx,
                  width: BOX_COL_WIDTH,
                  position: "absolute",
                  left: (idx + visibleRangeStart) * BOX_COL_WIDTH
                }}
                focused={p.name === focusedPartitionName}
                dimSuccesses={!options.colorizeByAge}
                onClick={() => setFocusedPartitionName(p.name)}
              >
                <TopLabelTilted>
                  <div className="tilted">{p.name}</div>
                </TopLabelTilted>
                {sortPartitionSteps(p.steps).map(({ name, color, unix }) => (
                  <div
                    key={name}
                    className={`square ${(options.showPrevious
                      ? color
                      : StatusSquareFinalColor[color] || color
                    ).toLowerCase()}`}
                    onMouseEnter={() => setHoveredStepName(name)}
                    onMouseLeave={() => setHoveredStepName("")}
                    style={
                      options.colorizeByAge
                        ? {
                            opacity:
                              unix >= colorizeSliceUnix
                                ? 0.3 + 0.7 * ((unix - minUnix) / (maxUnix - minUnix))
                                : 0.08
                          }
                        : {}
                    }
                  />
                ))}
                <Divider />
                <LeftLabel style={{ textAlign: "center" }}>{p.runs.length}</LeftLabel>
              </GridColumn>
            ))}
          </div>
        </GridScrollContainer>
      </div>
      {stepRows.length === 0 && <EmptyMessage>No data to display.</EmptyMessage>}
      <div style={{ padding: "10px 0" }}>
        <RunTable
          runs={focusedPartition ? focusedPartition.runs : []}
          onSetFilter={() => {}}
          nonIdealState={<div />}
        />
      </div>
    </PartitionRunMatrixContainer>
  );
};

const EmptyMessage = styled.div`
  padding: 20px;
  text-align: center;
`;

const PartitionRunMatrixContainer = styled.div`
  display: block;
`;

const OptionsContainer = styled.div`
  display: flex;
  align-items: center;
  padding: 6px 0;
`;

const Divider = styled.div`
  height: 1px;
  width: 100%;
  margin-top: 5px;
  border-top: 1px solid ${Colors.GRAY5};
`;

export const PARTITION_RUN_MATRIX_PIPELINE_QUERY = gql`
  query PartitionRunMatrixPipelineQuery($pipelineSelector: PipelineSelector) {
    pipelineSnapshotOrError(activePipelineSelector: $pipelineSelector) {
      ... on PipelineSnapshot {
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
        }
      }
    }
  }
`;

interface RunTagsTokenizingFieldProps {
  runs: Partition["runs"];
  tokens: TokenizingFieldValue[];
  onChange: (tokens: TokenizingFieldValue[]) => void;
}

function runsMatchingTagTokens(runs: Partition["runs"], tokens: TokenizingFieldValue[]) {
  return runs.filter(
    run =>
      tokens.length === 0 ||
      tokens.some(({ token, value }) => {
        if (token === "tag") {
          const [tkey, tvalue] = value.split("=");
          return run.tags.some(tag => tag.key === tkey && tag.value === tvalue);
        }
        throw new Error(`Unknown token: ${token}`);
      })
  );
}

const RunTagsTokenizingField: React.FunctionComponent<RunTagsTokenizingFieldProps> = ({
  runs,
  tokens,
  onChange
}) => {
  const suggestions = [
    {
      token: "tag",
      values: () => {
        const runTags = runs.map(r => r.tags).reduce((a, b) => [...a, ...b], []);
        const runTagValues = runTags.map(t => `${t.key}=${t.value}`);
        return uniq(runTagValues).sort();
      }
    }
  ];
  const search = tokenizedValuesFromString(stringFromValue(tokens), suggestions);
  return (
    <TokenizingField
      small
      values={search}
      onChange={onChange}
      placeholder="Filter partition runs..."
      suggestionProviders={suggestions}
      loading={false}
    />
  );
};

const SliceSlider: React.FunctionComponent<{
  maxUnix: number;
  minUnix: number;
  value: number;
  disabled: boolean;
  onChange: (val: number) => void;
}> = ({ minUnix, maxUnix, value, disabled, onChange }) => {
  const delta = maxUnix - minUnix;
  const timeout = React.useRef<NodeJS.Timeout>();

  return (
    <div style={{ width: 220 }}>
      <SliderWithHandleLabelOnly
        min={0}
        max={1}
        disabled={disabled}
        stepSize={0.01}
        labelRenderer={(value: number) => (
          <span style={{ whiteSpace: "nowrap" }}>
            Run Start &gt; <Timestamp unix={delta * value + minUnix} format="YYYY-MM-DD HH:mm" />
          </span>
        )}
        onChange={(values: number[]) => {
          if (timeout.current) clearTimeout(timeout.current);
          timeout.current = setTimeout(() => onChange(delta * values[0] + minUnix), 10);
        }}
      >
        <MultiSlider.Handle
          value={(value - minUnix) / delta}
          type="full"
          intentAfter={Intent.PRIMARY}
        />
      </SliderWithHandleLabelOnly>
    </div>
  );
};

const SliderWithHandleLabelOnly = styled(MultiSlider)`
  &.bp3-slider {
    height: 19px;
  }
  .bp3-slider-axis > .bp3-slider-label {
    display: none;
  }
  .bp3-slider-handle > .bp3-slider-label {
    display: none;
  }
  .bp3-slider-handle.bp3-active > .bp3-slider-label {
    display: initial;
  }
`;
