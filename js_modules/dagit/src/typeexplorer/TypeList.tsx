import {H3, UL} from '@blueprintjs/core';
import gql from 'graphql-tag';
import * as React from 'react';
import styled from 'styled-components/macro';

import {SectionInner, SidebarSection, SidebarSubhead, SidebarTitle} from 'src/SidebarComponents';
import TypeWithTooltip from 'src/TypeWithTooltip';
import {TypeListFragment} from 'src/typeexplorer/types/TypeListFragment';

interface ITypeListProps {
  types: Array<TypeListFragment>;
}

function groupTypes(types: Array<TypeListFragment>) {
  const groups = {
    Custom: Array<TypeListFragment>(),
    'Built-in': Array<TypeListFragment>(),
  };
  types.forEach((type) => {
    if (type.isBuiltin) {
      groups['Built-in'].push(type);
    } else {
      groups['Custom'].push(type);
    }
  });
  return groups;
}

export default class TypeList extends React.Component<ITypeListProps, {}> {
  static fragments = {
    TypeListFragment: gql`
      fragment TypeListFragment on DagsterType {
        name
        isBuiltin
        ...DagsterTypeWithTooltipFragment
      }

      ${TypeWithTooltip.fragments.DagsterTypeWithTooltipFragment}
    `,
  };

  renderTypes(types: TypeListFragment[]) {
    return types.map((type, i) => (
      <TypeLI key={i}>
        <TypeWithTooltip type={type} />
      </TypeLI>
    ));
  }

  render() {
    const groups = groupTypes(this.props.types);

    return (
      <>
        <SidebarSubhead />
        <SectionInner>
          <SidebarTitle>Pipeline Types</SidebarTitle>
        </SectionInner>
        {Object.keys(groups).map((title, idx) => (
          <SidebarSection key={idx} title={title} collapsedByDefault={idx !== 0}>
            <UL>{this.renderTypes(groups[title])}</UL>
          </SidebarSection>
        ))}
        <H3 />
      </>
    );
  }
}

const TypeLI = styled.li`
  text-overflow: ellipsis;
  overflow: hidden;
`;
