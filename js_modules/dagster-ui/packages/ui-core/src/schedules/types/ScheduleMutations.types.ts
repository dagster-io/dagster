// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type StartThisScheduleMutationVariables = Types.Exact<{
  scheduleSelector: Types.ScheduleSelector;
}>;

export type StartThisScheduleMutation = {
  __typename: 'Mutation';
  startSchedule:
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
        __typename: 'ScheduleStateResult';
        scheduleState: {
          __typename: 'InstigationState';
          id: string;
          selectorId: string;
          name: string;
          instigationType: Types.InstigationType;
          status: Types.InstigationStatus;
          runningCount: number;
        };
      }
    | {__typename: 'UnauthorizedError'; message: string};
};

export type StopScheduleMutationVariables = Types.Exact<{
  id: Types.Scalars['String']['input'];
}>;

export type StopScheduleMutation = {
  __typename: 'Mutation';
  stopRunningSchedule:
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
        __typename: 'ScheduleStateResult';
        scheduleState: {
          __typename: 'InstigationState';
          id: string;
          status: Types.InstigationStatus;
          runningCount: number;
        };
      }
    | {__typename: 'UnauthorizedError'; message: string};
};

export type ResetScheduleMutationVariables = Types.Exact<{
  scheduleSelector: Types.ScheduleSelector;
}>;

export type ResetScheduleMutation = {
  __typename: 'Mutation';
  resetSchedule:
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
        __typename: 'ScheduleStateResult';
        scheduleState: {
          __typename: 'InstigationState';
          id: string;
          status: Types.InstigationStatus;
          runningCount: number;
        };
      }
    | {__typename: 'UnauthorizedError'; message: string};
};

export const StartThisScheduleVersion = '85ef7cd6041adc25adff7ea24b2434e2a6dfae5700b3a8d5683ba069d81890a7';

export const StopScheduleVersion = 'd2d45e914fce611fa1adfffd488af554e29d4ee87220636fb841c668e4b83832';

export const ResetScheduleVersion = '4de0dab719e737defe9787ab0b0bcef44f5384c92b2dd1c0bc0942643681b09b';
