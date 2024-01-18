// Generated GraphQL types, do not edit manually.
import * as Types from '../../../graphql/types';

export type AssetGroupAndLocationQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
}>;

export type AssetGroupAndLocationQuery = {
  __typename: 'Query';
  assetOrError:
    | {
        __typename: 'Asset';
        id: string;
        definition: {
          __typename: 'AssetNode';
          id: string;
          groupName: string | null;
          repository: {
            __typename: 'Repository';
            id: string;
            name: string;
            location: {__typename: 'RepositoryLocation'; id: string; name: string};
          };
        } | null;
      }
    | {__typename: 'AssetNotFoundError'};
};
