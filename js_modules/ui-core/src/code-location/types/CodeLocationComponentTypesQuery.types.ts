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
    | {__typename: 'RepositoryLocationNotFound'; message: string};
};

export const CodeLocationComponentTypesQueryVersion = '1e28d6199105acb90e6c1d27ba70633db808324d6a0ffbe490bf0462645c6df6';
