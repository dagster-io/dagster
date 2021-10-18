import {gql} from '@apollo/client';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {Description} from '../pipelines/Description';
import {SidebarSection, SidebarSubhead, SidebarTitle} from '../pipelines/SidebarComponents';
import {Box} from '../ui/Box';

import {ConfigTypeSchema, CONFIG_TYPE_SCHEMA_FRAGMENT} from './ConfigTypeSchema';
import {TypeExplorerFragment} from './types/TypeExplorerFragment';

interface ITypeExplorerProps {
  isGraph: boolean;
  type: TypeExplorerFragment;
}

export const TypeExplorer: React.FC<ITypeExplorerProps> = (props) => {
  const {name, inputSchemaType, outputSchemaType, description} = props.type;
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
      <SidebarSection title={'Description'}>
        <Box padding={{vertical: 16, horizontal: 24}}>
          <Description description={description || 'No Description Provided'} />
        </Box>
      </SidebarSection>
      {inputSchemaType && (
        <SidebarSection title={'Input'}>
          <Box padding={{vertical: 16, horizontal: 24}}>
            <ConfigTypeSchema
              type={inputSchemaType}
              typesInScope={inputSchemaType.recursiveConfigTypes}
            />
          </Box>
        </SidebarSection>
      )}
      {outputSchemaType && (
        <SidebarSection title={'Output'}>
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
`;
