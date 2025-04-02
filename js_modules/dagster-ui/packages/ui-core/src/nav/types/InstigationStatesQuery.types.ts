// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstigationStatesQueryVariables = Types.Exact<{
  repositoryID: Types.Scalars['String']['input'];
}>;

export type InstigationStatesQuery = {
  __typename: 'Query';
  instigationStatesOrError:
    | {
        __typename: 'InstigationStates';
        results: Array<{
          __typename: 'InstigationState';
          id: string;
          selectorId: string;
          name: string;
          instigationType: Types.InstigationType;
          status: Types.InstigationStatus;
          runningCount: number;
        }>;
      }
    | {__typename: 'PythonError'; message: string; stack: Array<string>};
};

export const InstigationStatesQueryVersion = '98c41676dfb3c489e46455a3c2716e375050c9bed2d73e74c765453f2c63d0da';
