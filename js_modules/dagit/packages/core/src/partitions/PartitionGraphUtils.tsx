import {gql} from '@apollo/client';
import {Colors} from '@dagster-io/ui';
import isEqual from 'lodash/isEqual';
import * as React from 'react';
import styled from 'styled-components/macro';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {colorHash} from '../app/Util';

import {PartitionGraphFragment} from './types/PartitionGraphFragment';
export const PARTITION_GRAPH_FRAGMENT = gql`
  fragment PartitionGraphFragment on PipelineRun {
    id
    runId
    stats {
      ... on RunStatsSnapshot {
        id
        startTime
        endTime
        materializations
      }
      ...PythonErrorFragment
    }
    stepStats {
      __typename
      stepKey
      startTime
      endTime
      status
      materializations {
        __typename
      }
      expectationResults {
        success
      }
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

export const getPipelineDurationForRun = (run: PartitionGraphFragment) => {
  const {stats} = run;
  if (stats && stats.__typename === 'RunStatsSnapshot' && stats.endTime && stats.startTime) {
    return stats.endTime - stats.startTime;
  }

  return undefined;
};

export const getStepDurationsForRun = (run: PartitionGraphFragment) => {
  const {stepStats} = run;

  const perStepDuration = {};
  stepStats.forEach((stepStat: any) => {
    if (stepStat.endTime && stepStat.startTime) {
      perStepDuration[stepStat.stepKey] = stepStat.endTime - stepStat.startTime;
    }
  });

  return perStepDuration;
};

export const getPipelineMaterializationCountForRun = (run: PartitionGraphFragment) => {
  const {stats} = run;
  if (stats && stats.__typename === 'RunStatsSnapshot') {
    return stats.materializations;
  }
  return undefined;
};

export const getStepMaterializationCountForRun = (run: PartitionGraphFragment) => {
  const {stepStats} = run;
  const perStepCounts = {};
  stepStats.forEach((stepStat) => {
    perStepCounts[stepStat.stepKey] = stepStat.materializations?.length || 0;
  });
  return perStepCounts;
};

export const getPipelineExpectationSuccessForRun = (run: PartitionGraphFragment) => {
  const stepCounts: {[key: string]: number} = getStepExpectationSuccessForRun(run);
  return _arraySum(Object.values(stepCounts));
};

export const getStepExpectationSuccessForRun = (run: PartitionGraphFragment) => {
  const {stepStats} = run;
  const perStepCounts = {};
  stepStats.forEach((stepStat) => {
    perStepCounts[stepStat.stepKey] =
      stepStat.expectationResults?.filter((x) => x.success).length || 0;
  });
  return perStepCounts;
};

export const getPipelineExpectationFailureForRun = (run: PartitionGraphFragment) => {
  const stepCounts: {[key: string]: number} = getStepExpectationFailureForRun(run);
  return _arraySum(Object.values(stepCounts));
};

export const getStepExpectationFailureForRun = (run: PartitionGraphFragment) => {
  const {stepStats} = run;
  const perStepCounts = {};
  stepStats.forEach((stepStat) => {
    perStepCounts[stepStat.stepKey] =
      stepStat.expectationResults?.filter((x) => !x.success).length || 0;
  });
  return perStepCounts;
};

export const getPipelineExpectationRateForRun = (run: PartitionGraphFragment) => {
  const stepSuccesses: {
    [key: string]: number;
  } = getStepExpectationSuccessForRun(run);
  const stepFailures: {
    [key: string]: number;
  } = getStepExpectationFailureForRun(run);

  const pipelineSuccesses = _arraySum(Object.values(stepSuccesses));
  const pipelineFailures = _arraySum(Object.values(stepFailures));
  const pipelineTotal = pipelineSuccesses + pipelineFailures;

  return pipelineTotal ? pipelineSuccesses / pipelineTotal : 0;
};

export const getStepExpectationRateForRun = (run: PartitionGraphFragment) => {
  const {stepStats} = run;
  const perStepCounts = {};
  stepStats.forEach((stepStat) => {
    const results = stepStat.expectationResults || [];
    perStepCounts[stepStat.stepKey] = results.length
      ? results.filter((x) => x.success).length / results.length
      : 0;
  });
  return perStepCounts;
};

const _arraySum = (arr: number[]) => {
  let sum = 0;
  arr.forEach((x) => (sum += x));
  return sum;
};

export const StepSelector: React.FC<{
  all: string[];
  hidden: string[];
  onChangeHidden: (hidden: string[]) => void;
  isJob: boolean;
}> = ({all, hidden, isJob, onChangeHidden}) => {
  const jobLabel = isJob ? 'Total job' : 'Total pipeline';

  const onStepClick = (stepKey: string) => {
    return (evt: React.MouseEvent) => {
      if (evt.shiftKey) {
        // toggle on shift+click
        onChangeHidden(
          hidden.includes(stepKey) ? hidden.filter((s) => s !== stepKey) : [...hidden, stepKey],
        );
      } else {
        // regular click
        const allButClicked = all.filter((s) => s !== stepKey);

        if (isEqual(allButClicked, hidden)) {
          onChangeHidden([]);
        } else {
          onChangeHidden(allButClicked);
        }
      }
    };
  };

  return (
    <div style={{width: 330, flexShrink: 0}}>
      <StepsList>
        {[jobLabel, ...all].map((stepKey) => (
          <Item
            key={stepKey}
            shown={!hidden.includes(stepKey)}
            onClick={onStepClick(stepKey)}
            color={stepKey === jobLabel ? Colors.Gray500 : colorHash(stepKey)}
          >
            <div
              className="color-dot"
              style={{
                backgroundColor: !hidden.includes(stepKey)
                  ? stepKey === jobLabel
                    ? Colors.Gray500
                    : colorHash(stepKey)
                  : '#aaaaaa',
              }}
            />
            {stepKey}
          </Item>
        ))}
      </StepsList>
    </div>
  );
};

const StepsList = styled.div`
  padding-left: 24px;
`;

const Item = styled.div`
  list-style-type: none;
  cursor: pointer;
  text-decoration: ${({shown}: {shown: boolean}) => (shown ? 'none' : 'line-through')};
  user-select: none;
  font-size: 12px;
  line-height: 32px;
  color: ${(props) => (props.shown ? Colors.Gray900 : Colors.Gray400)};
  white-space: nowrap;
  align-items: center;
  display: flex;

  & .color-dot {
    display: inline-block;
    margin-right: 5px;
    height: 7px;
    width: 14px;
    border-radius: 2px;
  }
`;
