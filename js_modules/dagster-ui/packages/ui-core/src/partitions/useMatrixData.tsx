import {gql} from '../apollo-client';
import {
  PartitionMatrixSolidHandleFragment,
  PartitionMatrixStepRunFragment,
} from './types/useMatrixData.types';
import {filterByQuery} from '../app/GraphQueryImpl';
import {GanttChartLayout} from '../gantt/Constants';
import {GanttChartMode} from '../gantt/GanttChart';
import {buildLayout} from '../gantt/GanttChartLayout';
import {StepEventStatus} from '../graphql/types';
import {useThrottledMemo} from '../hooks/useThrottledMemo';
import {explodeCompositesInHandleGraph} from '../pipelines/CompositeSupport';
import {GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT} from '../pipelines/GraphExplorer';

export type StatusSquareColor =
  | 'SUCCESS'
  | 'FAILURE'
  | 'MISSING'
  | 'FAILURE-MISSING'
  | 'SUCCESS-MISSING';

export interface PartitionRuns {
  name: string;
  runsLoaded: boolean;
  runs: PartitionMatrixStepRunFragment[];
}

interface DisplayOptions {
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

const MISSING_STEP_STATUSES = new Set([StepEventStatus.IN_PROGRESS, StepEventStatus.SKIPPED]);

function getStartTime(a: PartitionMatrixStepRunFragment) {
  return a.startTime || 0;
}

function byStartTimeAsc(a: PartitionMatrixStepRunFragment, b: PartitionMatrixStepRunFragment) {
  return getStartTime(a) - getStartTime(b);
}

// BG Note: Dagster 0.10.0 removed the .compute step key suffix, but the Run Matrix takes the current
// step tree and looks up data for each step in historical runs. For continuity across 0.10.0, we
// match historical step keys with the .compute format as well. We can remove safely after 120 days?
function isStepKeyForNode(nodeName: string, stepKey: string) {
  const dynamicRegex = new RegExp(nodeName + DYNAMIC_STEP_REGEX_SUFFIX);
  return stepKey === nodeName || stepKey === `${nodeName}.compute` || stepKey.match(dynamicRegex);
}

function buildMatrixData(
  layout: GanttChartLayout,
  partitionNames: string[],
  partitionsByName: Record<string, PartitionRuns>,
  options?: DisplayOptions,
) {
  const partitionColumns = partitionNames.map((name, idx) => {
    const partition: PartitionRuns = (partitionsByName as any)[name] || {
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

      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const lastRun = partition.runs[partition.runs.length - 1]!;
      const lastRunStepStatus = lastRun.stepStats.find((stats) =>
        isStepKeyForNode(node.name, stats.stepKey),
      )?.status;

      let previousRunStatus;
      if (
        partition.runs.length > 1 &&
        (!lastRunStepStatus || MISSING_STEP_STATUSES.has(lastRunStepStatus))
      ) {
        let idx = partition.runs.length - 2;
        while (idx >= 0 && !previousRunStatus) {
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          const currRun = partition.runs[idx]!;
          const currRunStatus = currRun.stepStats.find((stats) =>
            isStepKeyForNode(node.name, stats.stepKey),
          )?.status;
          if (currRunStatus && !MISSING_STEP_STATUSES.has(currRunStatus)) {
            previousRunStatus = currRunStatus;
            break;
          }
          idx--;
        }
      }

      if (!lastRunStepStatus && !previousRunStatus) {
        return blankState;
      }

      const color: StatusSquareColor =
        !lastRunStepStatus || MISSING_STEP_STATUSES.has(lastRunStepStatus)
          ? (`${previousRunStatus}-MISSING` as StatusSquareColor)
          : (lastRunStepStatus as StatusSquareColor);
      return {
        name: node.name,
        unix: getStartTime(lastRun),
        color,
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
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const totalFailures = partitionColumns.filter((p) => p.steps[idx]!.color.includes('FAILURE'));
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const finalFailures = partitionColumns.filter((p) => p.steps[idx]!.color.endsWith('FAILURE'));
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
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      if (stepRows[ii]!.finalFailurePercent === 0) {
        stepRows.splice(ii, 1);
        partitionColumns.forEach((p) => p.steps.splice(ii, 1));
      }
    }
    for (let ii = partitionColumns.length - 1; ii >= 0; ii--) {
      if (
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        partitionColumns[ii]!.runs.length === 0 ||
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        partitionColumns[ii]!.steps.every((step) => step.color.includes('SUCCESS'))
      ) {
        partitionColumns.splice(ii, 1);
      }
    }
  }

  return {stepRows, partitionColumns};
}

interface MatrixDataInputs {
  solidHandles: PartitionMatrixSolidHandleFragment[] | false;
  partitionNames: string[];
  partitions: PartitionRuns[];
  stepQuery: string;
  options?: DisplayOptions;
}

export type MatrixData = ReturnType<typeof buildMatrixData>;

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
export const useMatrixData = ({
  solidHandles,
  stepQuery,
  partitionNames,
  partitions,
  options,
}: MatrixDataInputs) => {
  return useThrottledMemo(
    () => {
      const nodes = solidHandles
        ? explodeCompositesInHandleGraph(solidHandles).map((h) => h.solid)
        : [];
      // Filter the pipeline's structure and build the flat gantt layout for the left hand side
      const solidsFiltered = filterByQuery(nodes, stepQuery);
      const layout = buildLayout({nodes: solidsFiltered.all, mode: GanttChartMode.FLAT});
      const partitionsByName: Record<string, PartitionRuns> = {};
      partitions.forEach((p) => {
        // sort partition runs in place
        p.runs.sort(byStartTimeAsc);
        partitionsByName[p.name] = p;
      });
      // Build the matrix of step + partition squares - presorted to match the gantt layout
      return buildMatrixData(layout, partitionNames, partitionsByName, options);
    },
    [solidHandles, stepQuery, partitions, partitionNames, options],
    1000,
  );
};

export const PARTITION_MATRIX_STEP_RUN_FRAGMENT = gql`
  fragment PartitionMatrixStepRunFragment on Run {
    id
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
