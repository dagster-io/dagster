import * as React from "react";
import gql from "graphql-tag";
import { Link } from "react-router-dom";
import { ConfigTypeSchema } from "../ConfigTypeSchema";
import { TypeExplorerFragment } from "./types/TypeExplorerFragment";
import {
  SidebarSubhead,
  SidebarSection,
  SidebarTitle,
  SectionInner
} from "../SidebarComponents";

import Description from "../Description";

interface ITypeExplorerProps {
  type: TypeExplorerFragment;
}

export default class TypeExplorer extends React.Component<ITypeExplorerProps> {
  static fragments = {
    TypeExplorerFragment: gql`
      fragment TypeExplorerFragment on RuntimeType {
        name
        description
        inputSchemaType {
          ...ConfigTypeSchemaFragment
          innerTypes {
            ...ConfigTypeSchemaFragment
          }
        }
        outputSchemaType {
          ...ConfigTypeSchemaFragment
          innerTypes {
            ...ConfigTypeSchemaFragment
          }
        }
      }

      ${ConfigTypeSchema.fragments.ConfigTypeSchemaFragment}
    `
  };

  render() {
    const {
      name,
      inputSchemaType,
      outputSchemaType,
      description
    } = this.props.type;

    return (
      <div>
        <SidebarSubhead />
        <SectionInner>
          <SidebarTitle>
            <Link to="?types=true">Pipeline Types</Link> {">"} {name}
          </SidebarTitle>
        </SectionInner>
        <SidebarSection title={"Description"}>
          <Description description={description || "No Description Provided"} />
        </SidebarSection>
        {inputSchemaType && (
          <SidebarSection title={"Input"}>
            <ConfigTypeSchema
              type={inputSchemaType}
              typesInScope={inputSchemaType.innerTypes}
            />
          </SidebarSection>
        )}
        {outputSchemaType && (
          <SidebarSection title={"Output"}>
            <ConfigTypeSchema
              type={outputSchemaType}
              typesInScope={outputSchemaType.innerTypes}
            />
          </SidebarSection>
        )}
      </div>
    );
  }
}
