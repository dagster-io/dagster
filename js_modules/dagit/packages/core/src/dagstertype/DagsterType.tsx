import {gql} from '@apollo/client';
import {Box, Colors, FontFamily, Tag} from '@dagster-io/ui';
import {Spacing} from '@dagster-io/ui/src/components/types';
import * as React from 'react';
import styled from 'styled-components/macro';

import {gqlTypePredicate} from '../app/Util';
import {METADATA_ENTRY_FRAGMENT} from '../metadata/MetadataEntry';
import {TableSchema} from '../metadata/TableSchema';
import {MetadataEntryFragment} from '../metadata/types/MetadataEntryFragment';
import {Description} from '../pipelines/Description';
import {CONFIG_TYPE_SCHEMA_FRAGMENT} from '../typeexplorer/ConfigTypeSchema';

import {DagsterTypeFragment} from './types/DagsterTypeFragment';

export const dagsterTypeKind = (type: {metadataEntries: MetadataEntryFragment[]}) => {
  const tableSchema = type.metadataEntries.find(gqlTypePredicate('TableSchemaMetadataEntry'));
  if (tableSchema) {
    return 'table';
  } else {
    return 'standard';
  }
};

export const DagsterTypeKindTag: React.FC<{type: DagsterTypeFragment}> = (kind) => {
  return <Tag intent="primary">{kind}</Tag>;
};

const _DagsterTypeName: React.FC<{type: DagsterTypeFragment; className?: string}> = ({
  type,
  className,
}) => {
  const typeKind = dagsterTypeKind(type);
  const displayName = typeKind === 'standard' ? type.name : `${type.name} (${typeKind})`;
  return <Box className={className}>{displayName}</Box>;
};

export const DagsterTypeName = styled(_DagsterTypeName)`
  font-family: ${FontFamily.monospace};
  font-size: 16px;
  overflow: hidden;
  text-overflow: ellipsis;
`;

export const DagsterTypeSummary: React.FC<{
  type: DagsterTypeFragment;
  horizontalPadding?: Spacing;
}> = ({type, horizontalPadding}) => {
  horizontalPadding = horizontalPadding || 0;
  const tableSchemaEntry = type.metadataEntries.find(gqlTypePredicate('TableSchemaMetadataEntry'));
  return (
    <Box
      flex={{direction: 'column', gap: 8}}
      padding={{horizontal: 24, vertical: 16}}
      style={{overflowY: 'auto'}}
    >
      {type.name && (
        <Box>
          <DagsterTypeName type={type} />
        </Box>
      )}
      {type.description && (
        <Box padding={{horizontal: horizontalPadding}}>
          <Description description={type.description} />
        </Box>
      )}
      {tableSchemaEntry && (
        <Box
          border={{side: 'top', width: 1, color: Colors.KeylineGray}}
          style={{overflowY: 'auto', marginBottom: -12}}
          margin={{top: 4}}
        >
          <TableSchema schema={tableSchemaEntry.schema} itemHorizontalPadding={horizontalPadding} />
        </Box>
      )}
    </Box>
  );
};

// NOTE: Because you can't have a recursive fragment, inner types are limited.
export const DAGSTER_TYPE_FRAGMENT = gql`
  fragment DagsterTypeFragment on DagsterType {
    ..._DagsterTypeFragment
    innerTypes {
      ..._DagsterTypeFragment
    }
  }
  fragment _DagsterTypeFragment on DagsterType {
    key
    name
    displayName
    description
    isNullable
    isList
    isBuiltin
    isNothing
    metadataEntries {
      ...MetadataEntryFragment
    }
    inputSchemaType {
      ...ConfigTypeSchemaFragment
      recursiveConfigTypes {
        ...ConfigTypeSchemaFragment
      }
    }
    outputSchemaType {
      ...ConfigTypeSchemaFragment
      recursiveConfigTypes {
        ...ConfigTypeSchemaFragment
      }
    }
  }
  ${CONFIG_TYPE_SCHEMA_FRAGMENT}
  ${METADATA_ENTRY_FRAGMENT}
`;
