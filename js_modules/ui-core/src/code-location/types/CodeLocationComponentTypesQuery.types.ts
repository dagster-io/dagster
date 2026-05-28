// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type CodeLocationComponentTypesQueryVariables = Types.Exact<{
  locationName: Types.Scalars['String']['input'];
}>;

export type CodeLocationComponentTypesQuery = {
  __typename: 'Query';
  componentTypesForLocationOrError:
    | {
        __typename: 'ComponentTypes';
        locationName: string;
        componentTypes: Array<{
          __typename: 'ComponentTypeInfo';
          name: string;
          namespace: string;
          example: string;
          schema: any | null;
          description: string | null;
          owners: Array<string> | null;
          tags: Array<string> | null;
          isUiEditable: boolean;
        }>;
      }
    | {__typename: 'PythonError'; message: string}
    | {__typename: 'RepositoryLocationNotFound'; message: string};
};

export const CodeLocationComponentTypesQueryVersion = '28d380e6ebfb3161ceefa2312f57edf5955cc2949851cba28df2f913461a8816';
