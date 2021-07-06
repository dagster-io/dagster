import {gql} from '@apollo/client';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {Description} from '../pipelines/Description';
import {
  SectionInner,
  SidebarSection,
  SidebarSubhead,
  SidebarTitle,
} from '../pipelines/SidebarComponents';

import {ConfigTypeSchema, CONFIG_TYPE_SCHEMA_FRAGMENT} from './ConfigTypeSchema';
import {TypeExplorerFragment} from './types/TypeExplorerFragment';

interface ITypeExplorerProps {
  type: TypeExplorerFragment;
}

export const TypeExplorer: React.FC<ITypeExplorerProps> = (props) => {
  const {name, inputSchemaType, outputSchemaType, description} = props.type;
  return (
    <div>
      <SidebarSubhead />
      <SectionInner>
        <SidebarTitle>
          <Link to="?tab=types">Pipeline Types</Link> {'>'} {name}
        </SidebarTitle>
      </SectionInner>
      <SidebarSection title={'Description'}>
        <Description description={description || 'No Description Provided'} />
      </SidebarSection>
      {inputSchemaType && (
        <SidebarSection title={'Input'}>
          <ConfigTypeSchema
            type={inputSchemaType}
            typesInScope={inputSchemaType.recursiveConfigTypes}
          />
        </SidebarSection>
      )}
      {outputSchemaType && (
        <SidebarSection title={'Output'}>
          <ConfigTypeSchema
            type={outputSchemaType}
            typesInScope={outputSchemaType.recursiveConfigTypes}
          />
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
