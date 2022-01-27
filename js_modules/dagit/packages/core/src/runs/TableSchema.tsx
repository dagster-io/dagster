import * as React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP, Tag, TagWIP, Tooltip} from '../../../ui/src';

import {
  MetadataEntryFragment,
  MetadataEntryFragment_EventTableSchemaMetadataEntry,
  MetadataEntryFragment_EventTableSchemaMetadataEntry_schema,
  MetadataEntryFragment_EventTableSchemaMetadataEntry_schema_columns,
  MetadataEntryFragment_EventTableSchemaMetadataEntry_schema_columns_constraints,
  MetadataEntryFragment_EventTableSchemaMetadataEntry_schema_constraints,
} from './types/MetadataEntryFragment';

// TODO is there a better way to do this?
type TableSchemaType = MetadataEntryFragment_EventTableSchemaMetadataEntry_schema;
type Column = MetadataEntryFragment_EventTableSchemaMetadataEntry_schema_columns;
type TableConstraints = MetadataEntryFragment_EventTableSchemaMetadataEntry_schema_constraints;
type ColumnConstraints = MetadataEntryFragment_EventTableSchemaMetadataEntry_schema_columns_constraints;

const SectionHeader = styled.div`
  height: 24px;
  padding-left: 24px;
  padding-right: 8px;
  background: ${ColorsWIP.White};
  border-top: 1px solid ${ColorsWIP.KeylineGray};
  border-bottom: 1px solid ${ColorsWIP.KeylineGray};
  color: ${ColorsWIP.Gray900};
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  font-weight: 700;
  user-select: none;
`;

const ColumnItemContainer = styled.div`
  padding-top: 12px;
  padding-bottom: 12px;
  padding-left: 24px;
  padding-right: 8px;
  background: ${ColorsWIP.White};
  border-top: 1px solid ${ColorsWIP.KeylineGray};
  border-bottom: 1px solid ${ColorsWIP.KeylineGray};
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

const ColumnConstraintsTooltipContent = styled.div`
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 8px;
  div:first-child {
    border-top: none;
  }
`;

const ColumnConstraintsTooltipContentItem = styled.div`
  border-top: 1px solid ${ColorsWIP.KeylineGray};
  padding: 4px;
  width: 300px;
`;

const NonNullableTag = <TagWIP intent="warning">non-nullable</TagWIP>;

const UniqueTag = <TagWIP intent="success">unique</TagWIP>;

const OtherTag: React.FC<{other: string[]}> = ({other}) => {
  const content = (
    <ColumnConstraintsTooltipContent>
      {other.map((constraint, i) => (
        <ColumnConstraintsTooltipContentItem key={i}>
          {constraint}
        </ColumnConstraintsTooltipContentItem>
      ))}
    </ColumnConstraintsTooltipContent>
  );
  return (
    <Tooltip content={content}>
      <TagWIP intent="warning">
        {other.length} constraint{other.length === 1 ? '' : 's'}…
      </TagWIP>
    </Tooltip>
  );
};

const ColumnItem: React.FC<{
  name: string;
  description?: string;
  constraints: ColumnConstraints;
}> = ({name, description, constraints}) => {
  return (
    <ColumnItemContainer>
      <ColumnMetadata>
        <ColumnName>{name}</ColumnName>
        {!constraints.nullable && NonNullableTag}
        {constraints.unique && UniqueTag}
        {constraints.other?.length > 0 && <OtherTag other={constraints.other} />}
      </ColumnMetadata>
      {description && <ColumnDescription>{description}</ColumnDescription>}
    </ColumnItemContainer>
  );
};

export const isTableSchemaMetadataEntry = (
  metadataEntry: MetadataEntryFragment,
): metadataEntry is MetadataEntryFragment_EventTableSchemaMetadataEntry => {
  return metadataEntry.__typename === 'EventTableSchemaMetadataEntry';
};

export const TableSchema: React.FC<{
  schema: TableSchemaType;
}> = ({schema}) => {
  return (
    <div>
      <SectionHeader>columns</SectionHeader>
      {schema.columns.map((column) => {
        return (
          <ColumnItem
            key={column.name}
            name={column.name}
            description={column.description || undefined}
            constraints={column.constraints}
          />
        );
      })}
    </div>
  );
};
