import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { H3, UL } from "@blueprintjs/core";
import TypeWithTooltip from "../TypeWithTooltip";
import { TypeListFragment } from "./types/TypeListFragment";
import {
  SidebarSubhead,
  SidebarSection,
  SidebarTitle
} from "../SidebarComponents";

interface ITypeListProps {
  types: Array<TypeListFragment>;
}

function groupTypes(types: TypeListFragment[]) {
  const groups = {
    Custom: Array<TypeListFragment>(),
    Generated: Array<TypeListFragment>(),
    "Built-in": Array<TypeListFragment>()
  };
  types.forEach(type => {
    if (type.builtin) {
      groups["Built-in"].push(type);
    } else if (type.name.includes(".")) {
      groups["Generated"].push(type);
    } else {
      groups["Custom"].push(type);
    }
  });
  return groups;
}

export default class TypeList extends React.Component<ITypeListProps, {}> {
  static fragments = {
    TypeListFragment: gql`
      fragment TypeListFragment on Type {
        name
        builtin
        ...TypeWithTooltipFragment
      }

      ${TypeWithTooltip.fragments.TypeWithTooltipFragment}
    `
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
      <div>
        <SidebarSubhead />
        <SidebarTitle>Pipeline Types</SidebarTitle>
        {Object.keys(groups).map((title, idx) => (
          <SidebarSection title={title} collapsedByDefault={idx !== 0}>
            <UL>{this.renderTypes(groups[title])}</UL>
          </SidebarSection>
        ))}
        <H3 />
      </div>
    );
  }
}

const TypeLI = styled.li`
  text-overflow: ellipsis;
  overflow-x: hidden;
`;
