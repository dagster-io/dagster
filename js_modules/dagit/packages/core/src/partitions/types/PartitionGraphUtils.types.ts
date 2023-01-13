// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type PartitionGraphFragment = {
  __typename: 'Run';
  id: string;
  runId: string;
  stats:
    | {
        __typename: 'PythonError';
        message: string;
        stack: Array<string>;
        errorChain: Array<{
          __typename: 'ErrorChainLink';
          isExplicitLink: boolean;
          error: {__typename: 'PythonError'; message: string; stack: Array<string>};
        }>;
      }
    | {
        __typename: 'RunStatsSnapshot';
        id: string;
        startTime: number | null;
        endTime: number | null;
        materializations: number;
      };
  stepStats: Array<{
    __typename: 'RunStepStats';
    stepKey: string;
    startTime: number | null;
    endTime: number | null;
    status: Types.StepEventStatus | null;
    materializations: Array<{__typename: 'MaterializationEvent'}>;
    expectationResults: Array<{__typename: 'ExpectationResult'; success: boolean}>;
  }>;
};
