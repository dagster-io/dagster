// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunRequestFragment = {
  __typename: 'RunRequest';
  runConfigYaml: string;
  runKey: string | null;
  tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
  assetSelection: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
};
