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
          isAppManaged: boolean;
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

export const CodeLocationComponentTypesQueryVersion = '1251d454635c1ea869a39fbca4762ad2b42aa4a9a9e95020576e83237f09633c';
