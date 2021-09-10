import {gql} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import {isEqual} from 'lodash';
import * as React from 'react';
import styled from 'styled-components/macro';

import {useFeatureFlags} from '../app/Flags';
import {colorHash} from '../app/Util';

import {PartitionGraphFragment} from './types/PartitionGraphFragment';

export const PARTITION_GRAPH_FRAGMENT = gql`
  fragment PartitionGraphFragment on PipelineRun {
    id
    runId
    stats {
      ... on PipelineRunStatsSnapshot {
        id
        startTime
        endTime
        materializations
      }
      ... on PythonError {
        ...PythonErrorFragment
      }
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
`;

export const getPipelineDurationForRun = (run: PartitionGraphFragment) => {
  const {stats} = run;
  if (
    stats &&
    stats.__typename === 'PipelineRunStatsSnapshot' &&
    stats.endTime &&
    stats.startTime
  ) {
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
  if (stats && stats.__typename === 'PipelineRunStatsSnapshot') {
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
}> = ({all, hidden, onChangeHidden}) => {
  const {flagPipelineModeTuples} = useFeatureFlags();
  const jobLabel = flagPipelineModeTuples ? 'Total job' : 'Total pipeline';

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
    <>
      <NavSectionHeader>
        Run steps
        <div style={{flex: 1}} />
        <span style={{fontSize: 13, opacity: 0.5}}>Tip: Shift-click to multi-select</span>
      </NavSectionHeader>
      <NavSection>
        {[jobLabel, ...all].map((stepKey) => (
          <Item
            key={stepKey}
            shown={!hidden.includes(stepKey)}
            onClick={onStepClick(stepKey)}
            color={stepKey === jobLabel ? Colors.GRAY2 : colorHash(stepKey)}
          >
            <div
              style={{
                display: 'inline-block',
                marginRight: 5,
                borderRadius: 5,
                height: 10,
                width: 10,
                backgroundColor: !hidden.includes(stepKey)
                  ? stepKey === jobLabel
                    ? Colors.GRAY2
                    : colorHash(stepKey)
                  : '#aaaaaa',
              }}
            />
            {stepKey}
          </Item>
        ))}
      </NavSection>
    </>
  );
};

const NavSectionHeader = styled.div`
  border-bottom: 1px solid ${Colors.GRAY5};
  margin-bottom: 10px;
  padding-bottom: 5px;
  display: flex;
`;

const NavSection = styled.div`
  margin-bottom: 30px;
`;

const Item = styled.div`
  list-style-type: none;
  padding: 5px 2px;
  cursor: pointer;
  text-decoration: ${({shown}: {shown: boolean}) => (shown ? 'none' : 'line-through')};
  user-select: none;
  font-size: 12px;
  color: ${(props) => (props.shown ? props.color : '#aaaaaa')};
  white-space: nowrap;
`;
