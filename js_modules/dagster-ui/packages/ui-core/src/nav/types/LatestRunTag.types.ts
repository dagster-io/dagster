// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type LatestRunTagQueryVariables = Types.Exact<{
  runsFilter?: Types.InputMaybe<Types.RunsFilter>;
}>;

export type LatestRunTagQuery = {
  __typename: 'Query';
  pipelineRunsOrError:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {__typename: 'PythonError'}
    | {
        __typename: 'Runs';
        results: Array<{
          __typename: 'Run';
          id: string;
          status: Types.RunStatus;
          creationTime: number;
          startTime: number | null;
          endTime: number | null;
          updateTime: number | null;
        }>;
      };
};

export const LatestRunTagQueryVersion = '6b18755e69bb01ee63d4ef02333c219a8c935b087e938b5da89ca99b95824e60';
