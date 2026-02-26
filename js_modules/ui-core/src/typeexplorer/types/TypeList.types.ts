// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type TypeListFragment_ListDagsterType = {
  __typename: 'ListDagsterType';
  name: string | null;
  isBuiltin: boolean;
  displayName: string;
  description: string | null;
};

export type TypeListFragment_NullableDagsterType = {
  __typename: 'NullableDagsterType';
  name: string | null;
  isBuiltin: boolean;
  displayName: string;
  description: string | null;
};

export type TypeListFragment_RegularDagsterType = {
  __typename: 'RegularDagsterType';
  name: string | null;
  isBuiltin: boolean;
  displayName: string;
  description: string | null;
};

export type TypeListFragment =
  | TypeListFragment_ListDagsterType
  | TypeListFragment_NullableDagsterType
  | TypeListFragment_RegularDagsterType;
