// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type BlueprintManagerRootQueryVariables = Types.Exact<{
  blueprintManagerSelector: Types.BlueprintManagerSelector;
}>;

export type BlueprintManagerRootQuery = {
  __typename: 'Query';
  blueprintManagerOrError:
    | {
        __typename: 'BlueprintManager';
        id: string;
        name: string;
        schema: {__typename: 'JsonSchema'; schema: string} | null;
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
      };
};
