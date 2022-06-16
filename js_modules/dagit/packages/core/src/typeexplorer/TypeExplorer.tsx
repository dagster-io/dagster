import {gql} from '@apollo/client';
import {Box, ConfigTypeSchema} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {gqlTypePredicate} from '../app/Util';
import {dagsterTypeKind} from '../dagstertype/DagsterType';
import {METADATA_ENTRY_FRAGMENT} from '../metadata/MetadataEntry';
import {TableSchema} from '../metadata/TableSchema';
import {Description} from '../pipelines/Description';
import {SidebarSection, SidebarSubhead, SidebarTitle} from '../pipelines/SidebarComponents';

import {CONFIG_TYPE_SCHEMA_FRAGMENT} from './ConfigTypeSchema';
import {TypeExplorerFragment} from './types/TypeExplorerFragment';

interface ITypeExplorerProps {
  isGraph: boolean;
  type: TypeExplorerFragment;
}

export const TypeExplorer: React.FC<ITypeExplorerProps> = (props) => {
  const {name, metadataEntries, inputSchemaType, outputSchemaType, description} = props.type;
  const typeKind = dagsterTypeKind(props.type);
  const displayName = typeKind === 'standard' ? name : `${name} (${typeKind})`;
  const tableSchema = metadataEntries.find(gqlTypePredicate('TableSchemaMetadataEntry'))?.schema;
  return (
    <div>
      <SidebarSubhead />
      <Box padding={{vertical: 16, horizontal: 24}}>
        <SidebarTitle>
          <Link to="?tab=types">{props.isGraph ? 'Graph types' : 'Pipeline types'}</Link>
          {' > '}
          {displayName}
        </SidebarTitle>
      </Box>
      <SidebarSection title="Description">
        <Box padding={{vertical: 16, horizontal: 24}}>
          <Description description={description || 'No Description Provided'} />
        </Box>
      </SidebarSection>
      {tableSchema && (
        <SidebarSection title="Columns">
          <TableSchema schema={tableSchema} itemHorizontalPadding={24} />
        </SidebarSection>
      )}
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
