import * as React from "react";
import gql from "graphql-tag";
import SpacedCard from "../SpacedCard";
import { H3, H5, H6, Text, Colors, Code, UL } from "@blueprintjs/core";
import TypeWithTooltip from "../TypeWithTooltip";
import Description from "../Description";
import { TypeExplorerFragment } from "./types/TypeExplorerFragment";

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
        ... on CompositeType {
          fields {
            name
            description
            isOptional
            type {
              name
              ...TypeWithTooltipFragment
            }
          }
        }
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
                <TypeWithTooltip type={field.type} />
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
      <SpacedCard>
        <H3>{this.props.type.name}</H3>
        <Description description={this.props.type.description} />

        {this.renderFields()}
      </SpacedCard>
    );
  }
}
