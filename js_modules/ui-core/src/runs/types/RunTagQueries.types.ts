/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunTagKeysQueryVariables = Exact<{[key: string]: never}>;

export type RunTagKeysQuery = {
  __typename: 'Query';
  runTagKeysOrError:
    | {__typename: 'PythonError'}
    | {__typename: 'RunTagKeys'; keys: Array<string>}
    | null;
};

export type RunTagValuesQueryVariables = Exact<{
  tagKeys: Array<string> | string;
}>;

export type RunTagValuesQuery = {
  __typename: 'Query';
  runTagsOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'RunTags';
        tags: Array<{__typename: 'PipelineTagAndValues'; key: string; values: Array<string>}>;
      }
    | null;
};

export const RunTagKeysQueryVersion = '833a405f7cb8f30c0901bc8a272edb51ac5281ebdf563e3017eace5d6976b2a9';

export const RunTagValuesQueryVersion = '0c0a9998c215bb801eb0adcd5449c0ac4cf1e8efbc6d0fcc5fb6d76fcc95cb92';
