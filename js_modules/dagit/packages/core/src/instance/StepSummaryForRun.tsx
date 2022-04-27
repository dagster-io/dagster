import {gql, useQuery} from '@apollo/client';
import {Colors, CaptionMono} from '@dagster-io/ui';
import qs from 'qs';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {failedStatuses, inProgressStatuses} from '../runs/RunStatuses';
import {StepEventStatus} from '../types/globalTypes';

import {
  StepSummaryForRunQuery,
  StepSummaryForRunQueryVariables,
} from './types/StepSummaryForRunQuery';

interface Props {
  runId: string;
}

export const StepSummaryForRun = (props: Props) => {
  const {runId} = props;
  const {data} = useQuery<StepSummaryForRunQuery, StepSummaryForRunQueryVariables>(
    STEP_SUMMARY_FOR_RUN_QUERY,
    {variables: {runId}},
  );

  const run = data?.pipelineRunOrError;
  const status = run?.__typename === 'Run' ? run.status : null;

  const relevantSteps = React.useMemo(() => {
    if (run?.__typename !== 'Run') {
      return [];
    }

    const {status} = run;
    if (failedStatuses.has(status)) {
      return run.stepStats.filter((step) => step.status === StepEventStatus.FAILURE);
    }

    if (inProgressStatuses.has(status)) {
      return run.stepStats.filter((step) => step.status === StepEventStatus.IN_PROGRESS);
    }

    return [];
  }, [run]);

  const stepCount = relevantSteps.length;

  if (!stepCount || !status) {
    return null;
  }

  if (failedStatuses.has(status)) {
    if (stepCount === 1) {
      const step = relevantSteps[0];
      const query = step.endTime
        ? qs.stringify({focusedTime: Math.floor(step.endTime * 1000)}, {addQueryPrefix: true})
        : '';
      return (
        <CaptionMono color={Colors.Gray500}>
          Failed at <Link to={`/instance/runs/${runId}${query}`}>{step.stepKey}</Link>
        </CaptionMono>
      );
    }
    return (
      <CaptionMono color={Colors.Gray500}>
        Failed at <Link to={`/instance/runs/${runId}`}>{stepCount} steps</Link>
      </CaptionMono>
    );
  }

  if (inProgressStatuses.has(status)) {
    if (stepCount === 1) {
      const step = relevantSteps[0];
      const query = step.endTime
        ? qs.stringify({focusedTime: Math.floor(step.endTime * 1000)}, {addQueryPrefix: true})
        : '';
      return (
        <CaptionMono color={Colors.Gray500}>
          In progress at <Link to={`/instance/runs/${runId}${query}`}>{step.stepKey}</Link>
        </CaptionMono>
      );
    }
    return (
      <CaptionMono color={Colors.Gray500}>
        In progress at <Link to={`/instance/runs/${runId}`}>{stepCount} steps</Link>
      </CaptionMono>
    );
  }

  return null;
};

const STEP_SUMMARY_FOR_RUN_QUERY = gql`
  query StepSummaryForRunQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      ... on Run {
        id
        status
        stepStats {
          endTime
          stepKey
          status
        }
      }
    }
  }
`;
