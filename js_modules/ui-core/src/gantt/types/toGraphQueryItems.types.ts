/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type StepKind = 'COMPUTE' | 'UNRESOLVED_COLLECT' | 'UNRESOLVED_MAPPED';

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
