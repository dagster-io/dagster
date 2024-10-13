// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type TableSchemaFragment = {
  __typename: 'TableSchema';
  columns: Array<{
    __typename: 'TableColumn';
    name: string;
    description: string | null;
    type: string;
    constraints: {
      __typename: 'TableColumnConstraints';
      nullable: boolean;
      unique: boolean;
      other: Array<string>;
    };
    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
  }>;
  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
};

export type ConstraintsForTableColumnFragment = {
  __typename: 'TableColumnConstraints';
  nullable: boolean;
  unique: boolean;
  other: Array<string>;
};
