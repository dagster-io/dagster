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
        blueprints: Array<{
          __typename: 'Blueprint';
          id: string;
          key: {__typename: 'BlueprintKey'; managerName: string; identifierWithinManager: string};
          blob: {__typename: 'Blob'; value: string} | null;
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
      };
};

export type CreateBlueprintMutationVariables = Types.Exact<{
  blueprintManagerSelector: Types.BlueprintManagerSelector;
  blob: Types.Scalars['String']['input'];
  identifierWithinManager: Types.Scalars['String']['input'];
}>;

export type CreateBlueprintMutation = {__typename: 'Mutation'; createBlueprint: string};

export type UpdateBlueprintMutationVariables = Types.Exact<{
  blueprintManagerSelector: Types.BlueprintManagerSelector;
  blob: Types.Scalars['String']['input'];
  identifierWithinManager: Types.Scalars['String']['input'];
}>;

export type UpdateBlueprintMutation = {__typename: 'Mutation'; updateBlueprint: string};
