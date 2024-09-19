// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type DagsterTypeWithTooltipFragment_ListDagsterType = {
  __typename: 'ListDagsterType';
  name: string | null;
  displayName: string;
  description: string | null;
};

export type DagsterTypeWithTooltipFragment_NullableDagsterType = {
  __typename: 'NullableDagsterType';
  name: string | null;
  displayName: string;
  description: string | null;
};

export type DagsterTypeWithTooltipFragment_RegularDagsterType = {
  __typename: 'RegularDagsterType';
  name: string | null;
  displayName: string;
  description: string | null;
};

export type DagsterTypeWithTooltipFragment =
  | DagsterTypeWithTooltipFragment_ListDagsterType
  | DagsterTypeWithTooltipFragment_NullableDagsterType
  | DagsterTypeWithTooltipFragment_RegularDagsterType;
