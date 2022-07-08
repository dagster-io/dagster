import {gql} from '@apollo/client';
import {shallowCompareKeys} from '@blueprintjs/core/lib/cjs/common/utils';
import React from 'react';

import {filterByQuery} from '../app/GraphQueryImpl';
import {GanttChartLayout} from '../gantt/Constants';
import {GanttChartMode} from '../gantt/GanttChart';
import {buildLayout} from '../gantt/GanttChartLayout';
import {explodeCompositesInHandleGraph} from '../pipelines/CompositeSupport';
import {StepEventStatus} from '../types/globalTypes';

import {GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT} from '../pipelines/GraphExplorer';
import {PartitionMatrixStepRunFragment} from './types/PartitionMatrixStepRunFragment';
import {PartitionMatrixSolidHandleFragment} from './types/PartitionMatrixSolidHandleFragment';

type StatusSquareColor =
  | 'SUCCESS'
  | 'FAILURE'
  | 'SKIPPED'
  | 'MISSING'
  | 'FAILURE-SUCCESS'
  | 'FAILURE-SKIPPED'
  | 'SUCCESS-FAILURE'
  | 'SUCCESS-SKIPPED'
  | 'SKIPPED-SUCCESS'
  | 'SKIPPED-FAILURE';

export const StatusSquareFinalColor: {[key: string]: StatusSquareColor} = {
  'FAILURE-SUCCESS': 'SUCCESS',
  'SKIPPED-SUCCESS': 'SUCCESS',
  'SUCCESS-FAILURE': 'FAILURE',
  'SKIPPED-FAILURE': 'FAILURE',
  'FAILURE-SKIPPED': 'SKIPPED',
  'SUCCESS-SKIPPED': 'SKIPPED',
};

export interface PartitionRuns {
  name: string;
  runsLoaded: boolean;
  runs: PartitionMatrixStepRunFragment[];
}

export interface DisplayOptions {
  showFailuresAndGapsOnly: boolean;
  showPrevious: boolean;
  colorizeByAge: boolean;
  colorizeSliceUnix: number;
}

const DYNAMIC_STEP_REGEX_SUFFIX = '\\[.*\\]';

export interface MatrixStep {
  name: string;
  color: string;
  unix: number;
}

function getStartTime(a: PartitionMatrixStepRunFragment) {
  return a.startTime || 0;
}

function byStartTimeAsc(a: PartitionMatrixStepRunFragment, b: PartitionMatrixStepRunFragment) {
  return getStartTime(a) - getStartTime(b);
}

// BG Note: Dagit 0.10.0 removed the .compute step key suffix, but the Run Matrix takes the current
// step tree and looks up data for each step in historical runs. For continuity across 0.10.0, we
// match historical step keys with the .compute format as well. We can remove safely after 120 days?
export function isStepKeyForNode(nodeName: string, stepKey: string) {
  const dynamicRegex = new RegExp(nodeName + DYNAMIC_STEP_REGEX_SUFFIX);
  return stepKey === nodeName || stepKey === `${nodeName}.compute` || stepKey.match(dynamicRegex);
}

function buildMatrixData(
  layout: GanttChartLayout,
  partitionNames: string[],
  partitions: PartitionRuns[],
  options?: DisplayOptions,
) {
  const partitionsByName = {};
  partitions.forEach((p) => {
    // Note this is sorting partition runs in place, I don't think it matters and
    // seems better than cloning all the arrays.
    p.runs.sort(byStartTimeAsc);
    partitionsByName[p.name] = p;
  });

  const partitionColumns = partitionNames.map((name, idx) => {
    const partition: PartitionRuns = partitionsByName[name] || {
      name,
      runsLoaded: false,
      runs: [],
    };
    const steps = layout.boxes.map(({node}) => {
      const blankState = {
        name: node.name,
        color: 'MISSING' as StatusSquareColor,
        unix: 0,
      };

      if (!partition.runs.length) {
        return blankState;
      }

      const lastRun = partition.runs[partition.runs.length - 1];
      const lastRunStepStatus = lastRun.stepStats.find((stats) =>
        isStepKeyForNode(node.name, stats.stepKey),
      )?.status;

      if (!lastRunStepStatus || lastRunStepStatus === StepEventStatus.IN_PROGRESS) {
        return blankState;
      }

      return {
        name: node.name,
        unix: getStartTime(lastRun),
        color: lastRunStepStatus,
      };
    });
    return {
      ...partition,
      steps,
      idx,
    };
  });

  const partitionsWithARun = partitionColumns.filter((p) => p.runs.length > 0).length;

  const stepRows = layout.boxes.map((box, idx) => {
    const totalFailures = partitionColumns.filter((p) => p.steps[idx].color.includes('FAILURE'));
    const finalFailures = partitionColumns.filter((p) => p.steps[idx].color.endsWith('FAILURE'));
    return {
      x: box.x,
      name: box.node.name,
      totalFailurePercent: partitionsWithARun
        ? Math.round((totalFailures.length / partitionsWithARun) * 100)
        : 0,
      finalFailurePercent: partitionsWithARun
        ? Math.round((finalFailures.length / partitionsWithARun) * 100)
        : 0,
    };
  });

  if (options?.showFailuresAndGapsOnly) {
    for (let ii = stepRows.length - 1; ii >= 0; ii--) {
      if (stepRows[ii].finalFailurePercent === 0) {
        stepRows.splice(ii, 1);
        partitionColumns.forEach((p) => p.steps.splice(ii, 1));
      }
    }
    for (let ii = partitionColumns.length - 1; ii >= 0; ii--) {
      if (
        partitionColumns[ii].runs.length === 0 ||
        partitionColumns[ii].steps.every((step) => step.color.includes('SUCCESS'))
      ) {
        partitionColumns.splice(ii, 1);
      }
    }
  }

  return {stepRows, partitions, partitionColumns};
}

interface MatrixDataInputs {
  solidHandles: PartitionMatrixSolidHandleFragment[] | false;
  partitionNames: string[];
  partitions: PartitionRuns[];
  stepQuery: string;
  options?: DisplayOptions;
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
export const useMatrixData = (inputs: MatrixDataInputs) => {
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

  const nodes = explodeCompositesInHandleGraph(inputs.solidHandles).map((h) => h.solid);

  // Filter the pipeline's structure and build the flat gantt layout for the left hand side
  const solidsFiltered = filterByQuery(nodes, inputs.stepQuery);

  const layout = buildLayout({nodes: solidsFiltered.all, mode: GanttChartMode.FLAT});

  // Build the matrix of step + partition squares - presorted to match the gantt layout
  const result = buildMatrixData(layout, inputs.partitionNames, inputs.partitions, inputs.options);
  cachedMatrixData.current = {result, inputs};
  return result;
};

export const PARTITION_MATRIX_STEP_RUN_FRAGMENT = gql`
  fragment PartitionMatrixStepRunFragment on Run {
    id
    runId
    status
    startTime
    endTime
    stepStats {
      stepKey
      startTime
      endTime
      status
    }
    tags {
      key
      value
    }
  }
`;

export const PARTITION_MATRIX_SOLID_HANDLE_FRAGMENT = gql`
  fragment PartitionMatrixSolidHandleFragment on SolidHandle {
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
  ${GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT}
`;
