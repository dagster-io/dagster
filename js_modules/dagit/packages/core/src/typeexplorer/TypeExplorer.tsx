import {gql} from '@apollo/client';
import {Box, Heading, MetadataTable, Subheading, Table} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {Description} from '../pipelines/Description';
import {SidebarSection, SidebarSubhead, SidebarTitle} from '../pipelines/SidebarComponents';

import {ConfigTypeSchema, CONFIG_TYPE_SCHEMA_FRAGMENT} from './ConfigTypeSchema';
import {TypeExplorerFragment} from './types/TypeExplorerFragment';

import {MetadataEntry, METADATA_ENTRY_FRAGMENT} from '../runs/MetadataEntry';
import { isTableSchemaMetadataEntry, TableSchema } from '../runs/TableSchema';
import { MetadataEntryFragment } from '../runs/types/MetadataEntryFragment';

interface ITypeExplorerProps {
  isGraph: boolean;
  type: TypeExplorerFragment;
}

// TODO: how to put key on metadata entries?

export const TypeExplorer: React.FC<ITypeExplorerProps> = (props) => {
  const {name, metadataEntries, inputSchemaType, outputSchemaType, description} = props.type;
  const tableSchemaEntry = metadataEntries.find(isTableSchemaMetadataEntry);
  const tableSchema = tableSchemaEntry?.schema;
  return (
    <div>
      <SidebarSubhead />
      <Box padding={{vertical: 16, horizontal: 24}}>
        <SidebarTitle>
          <Link to="?tab=types">{props.isGraph ? 'Graph types' : 'Pipeline types'}</Link>
          {' > '}
          {name}
        </SidebarTitle>
      </Box>
      <SidebarSection title="Description">
        <Box padding={{vertical: 16, horizontal: 24}}>
          <Description description={description || 'No Description Provided'} />
        </Box>
        {tableSchema && (
            <TableSchema schema={tableSchema} />
        )}
      </SidebarSection>
      {inputSchemaType && (
        <SidebarSection title="Input">
          <Box padding={{vertical: 16, horizontal: 24}}>
            <ConfigTypeSchema
              type={inputSchemaType}
              typesInScope={inputSchemaType.recursiveConfigTypes}
            />
          </Box>
        </SidebarSection>
      )}
      {outputSchemaType && (
        <SidebarSection title="Output">
          <Box padding={{vertical: 16, horizontal: 24}}>
            <ConfigTypeSchema
              type={outputSchemaType}
              typesInScope={outputSchemaType.recursiveConfigTypes}
            />
          </Box>
        </SidebarSection>
      )}
    </div>
  );
};

// const ColumnDescription = React.FC<EventMetadata
// }>

export const TYPE_EXPLORER_FRAGMENT = gql`
  fragment TypeExplorerFragment on DagsterType {
    name
    description
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
  ${METADATA_ENTRY_FRAGMENT}
  ${CONFIG_TYPE_SCHEMA_FRAGMENT}
`;
