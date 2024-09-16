// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ConfigForRunQueryVariables = Types.Exact<{
  runId: Types.Scalars['ID']['input'];
}>;

export type ConfigForRunQuery = {
  __typename: 'Query';
  runOrError:
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
        __typename: 'Run';
        id: string;
        mode: string;
        runConfigYaml: string;
        solidSelection: Array<string> | null;
      }
    | {__typename: 'RunNotFoundError'};
};

export const ConfigForRunQueryVersion = '3c4bb0f771599d50a7e4c05b683f8f7b4b3f0ab844b85501bb85527707a4982a';
