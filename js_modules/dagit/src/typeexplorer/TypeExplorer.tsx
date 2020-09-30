import gql from 'graphql-tag';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {ConfigTypeSchema} from 'src/ConfigTypeSchema';
import Description from 'src/Description';
import {SectionInner, SidebarSection, SidebarSubhead, SidebarTitle} from 'src/SidebarComponents';
import {TypeExplorerFragment} from 'src/typeexplorer/types/TypeExplorerFragment';

interface ITypeExplorerProps {
  type: TypeExplorerFragment;
}

export default class TypeExplorer extends React.Component<ITypeExplorerProps> {
  static fragments = {
    TypeExplorerFragment: gql`
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

      ${ConfigTypeSchema.fragments.ConfigTypeSchemaFragment}
    `,
  };

  render() {
    const {name, inputSchemaType, outputSchemaType, description} = this.props.type;

    return (
      <div>
        <SidebarSubhead />
        <SectionInner>
          <SidebarTitle>
            <Link to="?types=true">Pipeline Types</Link> {'>'} {name}
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
  }
}
