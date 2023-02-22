// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunTagKeysQueryVariables = Types.Exact<{[key: string]: never}>;

export type RunTagKeysQuery = {__typename: 'DagitQuery'; runTagKeys: Array<string>};

export type RunTagValuesQueryVariables = Types.Exact<{
  tagKeys: Array<Types.Scalars['String']> | Types.Scalars['String'];
}>;

export type RunTagValuesQuery = {
  __typename: 'DagitQuery';
  runTags: Array<{__typename: 'PipelineTagAndValues'; key: string; values: Array<string>}>;
};
