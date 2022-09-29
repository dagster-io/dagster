import {Box, Colors, Tag, Tooltip} from '@dagster-io/ui';
import {Spacing} from '@dagster-io/ui/src/components/types';
import * as React from 'react';
import styled from 'styled-components/macro';

import {
  MetadataEntryFragment_TableSchemaMetadataEntry,
  MetadataEntryFragment_TableSchemaMetadataEntry_schema,
  MetadataEntryFragment_TableSchemaMetadataEntry_schema_columns_constraints,
} from './types/MetadataEntryFragment';

export type ITableSchemaMetadataEntry = MetadataEntryFragment_TableSchemaMetadataEntry;
export type ITableSchema = MetadataEntryFragment_TableSchemaMetadataEntry_schema;
type ColumnConstraints = MetadataEntryFragment_TableSchemaMetadataEntry_schema_columns_constraints;

const MAX_CONSTRAINT_TAG_CHARS = 30;

interface ITableSchemaProps {
  schema: ITableSchema;
  itemHorizontalPadding?: Spacing;
}

export const TableSchema: React.FC<ITableSchemaProps> = ({schema, itemHorizontalPadding}) => {
  const multiColumnConstraints = schema.constraints?.other || [];
  return (
    <div>
      {multiColumnConstraints.length > 0 && (
        <Box
          flex={{
            wrap: 'wrap',
            gap: 4,
            alignItems: 'center',
          }}
          padding={{horizontal: itemHorizontalPadding, vertical: 8}}
        >
          {multiColumnConstraints.map((constraint, i) => (
            <ArbitraryConstraintTag key={i} constraint={constraint} />
          ))}
        </Box>
      )}
      {schema.columns.map((column) => {
        return (
          <ColumnItem
            key={column.name}
            name={column.name}
            type={column.type}
            description={column.description || undefined}
            constraints={column.constraints}
            horizontalPadding={itemHorizontalPadding || 8}
          />
        );
      })}
    </div>
  );
};

const _ColumnItem: React.FC<{
  name: string;
  type: string;
  description?: string;
  constraints: ColumnConstraints;
  horizontalPadding: number;
  className?: string;
}> = ({name, type, description, constraints, className}) => {
  return (
    <div className={className}>
      <Box flex={{wrap: 'wrap', gap: 4, alignItems: 'center'}}>
        <ColumnName>{name}</ColumnName>
        <TypeTag type={type} />
        {!constraints.nullable && NonNullableTag}
        {constraints.unique && UniqueTag}
        {constraints.other.map((constraint, i) => (
          <ArbitraryConstraintTag key={i} constraint={constraint} />
        ))}
      </Box>
      {description && <Box>{description}</Box>}
    </div>
  );
};

const ColumnItem = styled(_ColumnItem)`
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px ${(props) => props.horizontalPadding}px;
  border-top: 1px solid ${Colors.KeylineGray};
  :first-child {
    border-top: none;
  }
  font-size: 12px;
`;

const ColumnName = styled.div`
  font-weight: 600;
  padding-right: 4px;
`;

const TypeTag: React.FC<{type: string}> = ({type}) => <Tag intent="none">{type}</Tag>;

const NonNullableTag = <Tag intent="primary">non-nullable</Tag>;

const UniqueTag = <Tag intent="primary">unique</Tag>;

const ArbitraryConstraintTag: React.FC<{constraint: string}> = ({constraint}) => {
  if (constraint.length > MAX_CONSTRAINT_TAG_CHARS) {
    const content = constraint.substring(0, MAX_CONSTRAINT_TAG_CHARS - 3) + '...';
    return (
      <Tooltip content={<div>{constraint}</div>}>
        <Tag intent="primary">{content}</Tag>
      </Tooltip>
    );
  } else {
    return <Tag intent="primary">{constraint}</Tag>;
  }
};
