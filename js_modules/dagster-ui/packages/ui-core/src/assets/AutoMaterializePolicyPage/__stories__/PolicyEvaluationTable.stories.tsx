import * as React from 'react';

import {buildAssetConditionEvaluationRecord} from '../../../graphql/types';
import {PolicyEvaluationTable} from '../PolicyEvaluationTable';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Details/Automaterialize/PolicyEvaluationTable',
  component: PolicyEvaluationTable,
};

export const NonPartitioned = () => {
  const evaluation = buildAssetConditionEvaluationRecord({
    startTimestamp: 1,
    endTimestamp: 200,
  });

  return <PolicyEvaluationTable evaluationRecord={evaluation as any} selectPartition={() => {}} />;
};

export const Partitioned = () => {
  const evaluation = buildAssetConditionEvaluationRecord({
    startTimestamp: 1,
    endTimestamp: 200,
  });

  return <PolicyEvaluationTable evaluationRecord={evaluation as any} selectPartition={() => {}} />;
};

export const SpecificPartition = () => {
  const evaluation = buildAssetConditionEvaluationRecord({
    startTimestamp: 1,
    endTimestamp: 200,
  });

  return <PolicyEvaluationTable evaluationRecord={evaluation as any} selectPartition={() => {}} />;
};
