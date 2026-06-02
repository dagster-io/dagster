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
          formSchema: {__typename: 'ComponentFormSchema'; dataSchema: any; uiSchema: any} | null;
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

export const CodeLocationComponentTypesQueryVersion = '2adaf5e2bbca06f7fcdeb9139df9f0a3bf11c5c1f47c7166f96e1cb5c8266924';
