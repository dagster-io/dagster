// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type DagsterTypeWithTooltipFragment_ListDagsterType_ = {
  __typename: 'ListDagsterType';
  name: string | null;
  displayName: string;
  description: string | null;
};

export type DagsterTypeWithTooltipFragment_NullableDagsterType_ = {
  __typename: 'NullableDagsterType';
  name: string | null;
  displayName: string;
  description: string | null;
};

export type DagsterTypeWithTooltipFragment_RegularDagsterType_ = {
  __typename: 'RegularDagsterType';
  name: string | null;
  displayName: string;
  description: string | null;
};

export type DagsterTypeWithTooltipFragment =
  | DagsterTypeWithTooltipFragment_ListDagsterType_
  | DagsterTypeWithTooltipFragment_NullableDagsterType_
  | DagsterTypeWithTooltipFragment_RegularDagsterType_;
