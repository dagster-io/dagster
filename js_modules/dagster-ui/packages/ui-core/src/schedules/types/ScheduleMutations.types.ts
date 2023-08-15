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
          status: Types.InstigationStatus;
          runningCount: number;
        };
      }
    | {__typename: 'UnauthorizedError'; message: string};
};

export type StopScheduleMutationVariables = Types.Exact<{
  scheduleOriginId: Types.Scalars['String'];
  scheduleSelectorId: Types.Scalars['String'];
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
