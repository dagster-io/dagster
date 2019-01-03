import * as React from "react";
import gql from "graphql-tag";
import { Link } from "react-router-dom";
import TypeWithTooltip from "../TypeWithTooltip";
import TypeSchema from "../TypeSchema";
import { TypeExplorerFragment } from "./types/TypeExplorerFragment";
import {
  SidebarSubhead,
  SidebarSection,
  SidebarTitle
} from "../SidebarComponents";

interface ITypeExplorerProps {
  type: TypeExplorerFragment;
}

export default class TypeExplorer extends React.Component<ITypeExplorerProps> {
  static fragments = {
    TypeExplorerFragment: gql`
      fragment TypeExplorerFragment on Type {
        name
        ...TypeSchemaFragment
      }

      ${TypeSchema.fragments.TypeSchemaFragment}
    `
  };

  render() {
    return (
      <div>
        <SidebarSubhead />
        <SidebarTitle>
          <Link to="?types=true">Pipeline Types</Link> > {this.props.type.name}
        </SidebarTitle>
        <SidebarSection title={"Description"}>
          <TypeSchema type={this.props.type} />
        </SidebarSection>
      </div>
    );
  }
}
