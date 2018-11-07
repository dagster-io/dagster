import * as React from "react";
import gql from "graphql-tag";
import { UL } from "@blueprintjs/core";
import { Link } from "react-router-dom";
import TypeWithTooltip from "../TypeWithTooltip";
import Description from "../Description";
import { TypeExplorerFragment } from "./types/TypeExplorerFragment";
import {
  SidebarSubhead,
  SidebarSection,
  SidebarTitle
} from "../SidebarComponents";

interface ITypeExplorerProps {
  type: TypeExplorerFragment;
}

export default class TypeExplorer extends React.Component<
  ITypeExplorerProps,
  {}
> {
  static fragments = {
    TypeExplorerFragment: gql`
      fragment TypeExplorerFragment on Type {
        __typename
        name
        description
        typeAttributes {
          isBuiltin
          isSystemConfig
        }
        ... on CompositeType {
          fields {
            name
            description
            isOptional
            defaultValue
            type {
              ...TypeWithTooltipFragment
            }
          }
        }
        ...TypeWithTooltipFragment
      }

      ${TypeWithTooltip.fragments.TypeWithTooltipFragment}
    `
  };

  renderFields() {
    if (this.props.type.__typename === "CompositeType") {
      return (
        <UL>
          {this.props.type.fields.map((field, i) => {
            return (
              <li key={i}>
                {field.name} {field.isOptional ? "(optional)" : null}{" "}
                <TypeWithTooltip link={true} type={field.type} />
                <Description description={field.description} />
              </li>
            );
          })}
        </UL>
      );
    } else {
      return null;
    }
  }

  render() {
    return (
      <div>
        <SidebarSubhead />
        <SidebarTitle>
          <Link to="?types=true">Pipeline Types</Link> > {this.props.type.name}
        </SidebarTitle>
        <SidebarSection title={"Description"}>
          <Description description={this.props.type.description} />
        </SidebarSection>
        <SidebarSection title={"Fields"}>{this.renderFields()}</SidebarSection>
      </div>
    );
  }
}
