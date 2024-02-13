// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RepositoryInfoFragment = {
  __typename: 'Repository';
  id: string;
  name: string;
  location: {__typename: 'RepositoryLocation'; id: string; name: string};
  displayMetadata: Array<{__typename: 'RepositoryMetadata'; key: string; value: string}>;
};
