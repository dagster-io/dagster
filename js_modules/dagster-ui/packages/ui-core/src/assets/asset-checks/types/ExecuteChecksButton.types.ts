// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type ExecuteChecksButtonCheckFragment = {
  __typename: 'AssetCheck';
  name: string;
  canExecuteIndividually: Types.AssetCheckCanExecuteIndividually;
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
