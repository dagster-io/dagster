import * as React from "react";
import gql from "graphql-tag";
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

export default class TypeList extends React.Component<ITypeListProps, {}> {
  static fragments = {
    TypeListFragment: gql`
      fragment TypeListFragment on Type {
        name

        ...TypeWithTooltipFragment
      }

      ${TypeWithTooltip.fragments.TypeWithTooltipFragment}
    `
  };

  renderTypes() {
    return this.props.types.map((type, i) => (
      <li key={i}>
        <TypeWithTooltip type={type} />
      </li>
    ));
  }

  render() {
    return (
      <div>
        <SidebarSubhead />
        <SidebarTitle>Pipeline Types</SidebarTitle>
        <SidebarSection title={"Fields"}>
          <UL>{this.renderTypes()}</UL>
        </SidebarSection>
        <H3 />
      </div>
    );
  }
}
