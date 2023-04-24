// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunTagKeysNewQueryVariables = Types.Exact<{[key: string]: never}>;

export type RunTagKeysNewQuery = {
  __typename: 'DagitQuery';
  runTagKeysOrError:
    | {__typename: 'PythonError'}
    | {__typename: 'RunTagKeys'; keys: Array<string>}
    | null;
};

export type RunTagValuesNewQueryVariables = Types.Exact<{
  tagKeys: Array<Types.Scalars['String']> | Types.Scalars['String'];
}>;

export type RunTagValuesNewQuery = {
  __typename: 'DagitQuery';
  runTagsOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'RunTags';
        tags: Array<{__typename: 'PipelineTagAndValues'; key: string; values: Array<string>}>;
      }
    | null;
};
