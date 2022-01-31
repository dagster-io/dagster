import * as React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP, TagWIP, Tooltip} from '../../../ui/src';

import {IMetadataEntries} from './MetadataEntry';
import {
  MetadataEntryFragment,
  MetadataEntryFragment_EventTableSchemaMetadataEntry,
  MetadataEntryFragment_EventTableSchemaMetadataEntry_schema,
  MetadataEntryFragment_EventTableSchemaMetadataEntry_schema_columns_constraints,
} from './types/MetadataEntryFragment';

export type TTableSchemaMetadataEntry = MetadataEntryFragment_EventTableSchemaMetadataEntry;
export type TTableSchema = MetadataEntryFragment_EventTableSchemaMetadataEntry_schema;
type ColumnConstraints = MetadataEntryFragment_EventTableSchemaMetadataEntry_schema_columns_constraints;

const ColumnItemContainer = styled.div`
  padding-top: 12px;
  padding-bottom: 12px;
  padding-left: 8px;
  padding-right: 8px;
  border-top: 1px solid ${ColorsWIP.KeylineGray};
  :first-child {
    border-top: none;
  }
  color: ${ColorsWIP.Gray900};
  cursor: pointer;
  justify-content: start;
  align-items: center;
  font-size: 12px;
  user-select: none;
`;

const ColumnMetadata = styled.div`
  display: inline-flex;
  gap: 4px;
  align-items: center;
  flex-wrap: wrap;
`;

const ColumnName = styled.div`
  font-weight: 700;
  padding-right: 4px;
  align-items: center;
`;

const ColumnDescription = styled.div`
  margin-top: 4px;
  color: ${ColorsWIP.Gray700};
`;

const TypeTag: React.FC<{type: string}> = ({type}) => <TagWIP intent="none">{type}</TagWIP>;

const NonNullableTag = <TagWIP intent="warning">non-nullable</TagWIP>;

const UniqueTag = <TagWIP intent="success">unique</TagWIP>;

const MAX_BADGE_CHARS = 30;

const ArbitraryConstraintTag: React.FC<{constraint: string}> = ({constraint}) => {
  if (constraint.length > MAX_BADGE_CHARS) {
    const content = constraint.substring(0, MAX_BADGE_CHARS - 3) + '...';
    return (
      <Tooltip content={<div>{constraint}</div>}>
        <TagWIP intent="warning">{content}</TagWIP>
      </Tooltip>
    );
  } else {
    return <TagWIP intent="warning">{constraint}</TagWIP>;
  }
};

const ColumnItem: React.FC<{
  name: string;
  type: string;
  description?: string;
  constraints: ColumnConstraints;
}> = ({name, type, description, constraints}) => {
  return (
    <ColumnItemContainer>
      <ColumnMetadata>
        <ColumnName>{name}</ColumnName>
        <TypeTag type={type} />
        {!constraints.nullable && NonNullableTag}
        {constraints.unique && UniqueTag}
        {constraints.other.map((constraint, i) => (
          <ArbitraryConstraintTag key={i} constraint={constraint} />
        ))}
      </ColumnMetadata>
      {description && <ColumnDescription>{description}</ColumnDescription>}
    </ColumnItemContainer>
  );
};

export const hasTableSchema = (obj: IMetadataEntries): boolean => {
  return obj.metadataEntries.find(isTableSchemaMetadataEntry) !== undefined;
};

export const isTableSchemaMetadataEntry = (
  metadataEntry: MetadataEntryFragment,
): metadataEntry is MetadataEntryFragment_EventTableSchemaMetadataEntry => {
  return metadataEntry.__typename === 'EventTableSchemaMetadataEntry';
};

export const TableSchema: React.FC<{
  schema: TTableSchema;
}> = ({schema}) => {
  return (
    <div>
      {schema.columns.map((column) => {
        return (
          <ColumnItem
            key={column.name}
            name={column.name}
            type={column.type}
            description={column.description || undefined}
            constraints={column.constraints}
          />
        );
      })}
    </div>
  );
};
