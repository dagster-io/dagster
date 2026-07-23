/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type AssetCheckCanExecuteIndividually =
  | 'CAN_EXECUTE'
  | 'NEEDS_USER_CODE_UPGRADE'
  | 'REQUIRES_MATERIALIZATION';

export type ExecuteChecksButtonCheckFragment = {
  __typename: 'AssetCheck';
  name: string;
  canExecuteIndividually: Types.AssetCheckCanExecuteIndividually;
  jobNames: Array<string>;
};

export type ExecuteChecksButtonAssetNodeFragment = {
  __typename: 'AssetNode';
  id: string;
  jobNames: Array<string>;
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
  repository: {
    __typename: 'Repository';
    id: string;
    name: string;
    location: {__typename: 'RepositoryLocation'; id: string; name: string};
  };
};
