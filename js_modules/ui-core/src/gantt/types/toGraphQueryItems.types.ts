// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ExecutionPlanToGraphFragment = {
  __typename: 'ExecutionPlan';
  steps: Array<{
    __typename: 'ExecutionStep';
    key: string;
    kind: Types.StepKind;
    inputs: Array<{
      __typename: 'ExecutionStepInput';
      dependsOn: Array<{__typename: 'ExecutionStep'; key: string; kind: Types.StepKind}>;
    }>;
  }>;
};
