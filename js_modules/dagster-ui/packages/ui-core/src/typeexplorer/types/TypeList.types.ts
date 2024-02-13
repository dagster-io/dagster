// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type TypeListFragment_ListDagsterType_ = {
  __typename: 'ListDagsterType';
  name: string | null;
  isBuiltin: boolean;
  displayName: string;
  description: string | null;
};

export type TypeListFragment_NullableDagsterType_ = {
  __typename: 'NullableDagsterType';
  name: string | null;
  isBuiltin: boolean;
  displayName: string;
  description: string | null;
};

export type TypeListFragment_RegularDagsterType_ = {
  __typename: 'RegularDagsterType';
  name: string | null;
  isBuiltin: boolean;
  displayName: string;
  description: string | null;
};

export type TypeListFragment =
  | TypeListFragment_ListDagsterType_
  | TypeListFragment_NullableDagsterType_
  | TypeListFragment_RegularDagsterType_;
