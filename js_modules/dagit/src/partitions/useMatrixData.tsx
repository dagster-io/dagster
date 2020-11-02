import {shallowCompareKeys} from '@blueprintjs/core/lib/cjs/common/utils';
import React from 'react';

import {filterByQuery} from 'src/GraphQueryImpl';
import {TokenizingFieldValue} from 'src/TokenizingField';
import {formatStepKey} from 'src/Util';
import {GaantChartLayout} from 'src/gaant/Constants';
import {GaantChartMode} from 'src/gaant/GaantChart';
import {buildLayout} from 'src/gaant/GaantChartLayout';
import {PartitionRunMatrixPartitionFragment} from 'src/partitions/types/PartitionRunMatrixPartitionFragment';
import {PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles} from 'src/partitions/types/PartitionRunMatrixPipelineQuery';
import {StepEventStatus} from 'src/types/globalTypes';

type Partition = PartitionRunMatrixPartitionFragment;
type SolidHandle = PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles;

export type StatusSquareColor =
  | 'SUCCESS'
  | 'FAILURE'
  | 'FAILURE-SUCCESS'
  | 'SKIPPED'
  | 'SKIPPED-SUCCESS'
  | 'MISSING'
  | 'MISSING-SUCCESS';

export const StatusSquareFinalColor: {[key: string]: StatusSquareColor} = {
  'FAILURE-SUCCESS': 'SUCCESS',
  'SKIPPED-SUCCESS': 'SUCCESS',
  'MISSING-SUCCESS': 'SUCCESS',
};

export interface DisplayOptions {
  showFailuresAndGapsOnly: boolean;
  showPrevious: boolean;
  colorizeByAge: boolean;
}

export interface MatrixStep {
  name: string;
  color: string;
  unix: number;
}

function getStartTime(a: Partition['runs'][0]) {
  return ('startTime' in a.stats && a.stats.startTime) || 0;
}

function byStartTimeAsc(a: Partition['runs'][0], b: Partition['runs'][0]) {
  return getStartTime(a) - getStartTime(b);
}

function runsMatchingTagTokens(runs: Partition['runs'], tokens: TokenizingFieldValue[]) {
  return runs.filter(
    (run) =>
      tokens.length === 0 ||
      tokens.some(({token, value}) => {
        if (token === 'tag') {
          const [tkey, tvalue] = value.split('=');
          return run.tags.some((tag) => tag.key === tkey && tag.value === tvalue);
        }
        throw new Error(`Unknown token: ${token}`);
      }),
  );
}

function buildMatrixData(
  layout: GaantChartLayout,
  partitions: Partition[],
  options: DisplayOptions,
) {
  // Note this is sorting partition runs in place, I don't think it matters and
  // seems better than cloning all the arrays.
  partitions.forEach((p) => p.runs.sort(byStartTimeAsc));

  const partitionColumns = partitions.map((p) => ({
    name: p.name,
    runs: p.runs,
    steps: layout.boxes.map(({node}) => {
      const statuses = p.runs.map(
        (r) => r.stepStats.find((stats) => formatStepKey(stats.stepKey) === node.name)?.status,
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

      let color: StatusSquareColor = statuses[0] || 'MISSING';

      if (statuses.length > 1 && lastSuccessIdx !== -1) {
        const prev = statuses.slice(0, lastSuccessIdx);
        color = prev.includes(StepEventStatus.FAILURE)
          ? 'FAILURE-SUCCESS'
          : prev.includes(StepEventStatus.SKIPPED)
          ? 'SKIPPED-SUCCESS'
          : prev.includes(undefined)
          ? 'MISSING-SUCCESS'
          : 'SUCCESS';
      } else if (statuses.length > 1) {
        color = statuses.includes(StepEventStatus.FAILURE) ? 'FAILURE' : color;
      }

      return {
        name: node.name,
        color,
        unix,
      };
    }),
  }));

  const stepRows = layout.boxes.map((box, idx) => {
    const totalFailures = partitionColumns.filter((p) => p.steps[idx].color.includes('FAILURE'));
    const finalFailures = partitionColumns.filter((p) => p.steps[idx].color.endsWith('FAILURE'));
    return {
      x: box.x,
      name: box.node.name,
      totalFailurePercent: Math.round((totalFailures.length / partitionColumns.length) * 100),
      finalFailurePercent: Math.round((finalFailures.length / partitionColumns.length) * 100),
    };
  });

  if (options.showFailuresAndGapsOnly) {
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

  // Filter the runs down to the subset matching the tags input (eg: backfillId)
  const partitionsFiltered = inputs.partitions.map((p) => ({
    ...p,
    runs: runsMatchingTagTokens(p.runs, inputs.runsFilter),
  }));

  // Filter the pipeline's structure and build the flat gaant layout for the left hand side
  const solidsFiltered = filterByQuery(
    inputs.solidHandles.map((h) => h.solid),
    inputs.stepQuery,
  );
  const layout = buildLayout({nodes: solidsFiltered.all, mode: GaantChartMode.FLAT});

  // Build the matrix of step + partition squares - presorted to match the gaant layout
  const result = buildMatrixData(layout, partitionsFiltered, inputs.options);
  cachedMatrixData.current = {result, inputs};
  return result;
};
