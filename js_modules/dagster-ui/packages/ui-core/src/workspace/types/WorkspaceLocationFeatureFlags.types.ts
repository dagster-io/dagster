// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type LocationFeatureFlagsQueryVariables = Types.Exact<{
  name: Types.Scalars['String']['input'];
}>;

export type LocationFeatureFlagsQuery = {
  __typename: 'Query';
  workspaceLocationEntryOrError:
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
        __typename: 'WorkspaceLocationEntry';
        id: string;
        featureFlags: Array<{__typename: 'FeatureFlag'; name: string; enabled: boolean}>;
      }
    | null;
};
