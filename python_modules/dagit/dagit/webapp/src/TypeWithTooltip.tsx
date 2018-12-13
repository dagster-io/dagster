import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Link } from "react-router-dom";
import { Text } from "@blueprintjs/core";
import { TypeWithTooltipFragment } from "./types/TypeWithTooltipFragment";

interface ITypeWithTooltipProps {
  type: TypeWithTooltipFragment;
  link?: Boolean;
}

export default class TypeWithTooltip extends React.Component<
  ITypeWithTooltipProps,
  {}
> {
  static fragments = {
    TypeWithTooltipFragment: gql`
      fragment TypeWithTooltipFragment on Type {
        name
        description
        typeAttributes {
          isNamed
        }
      }
    `
  };

  render() {
    // This is a temporary degradation that prevents
    // the user from instigating crashes. What we are
    // going to want to end up having rendering such as
    // [[Int]] for double nested lists
    // or
    // {
    //    foo: Int?
    //    bar: [String]
    //    nested_dict: {
    //      nested_field: Bool
    //    }
    // }
    // for anonymous dicts

    // HACK HACK HACK
    // Until the types are printed out using a nice definition
    // language (like the one above) we are going to hide
    // anonymous dict names from the UI
    if (this.props.type.name.startsWith("Dict_")) {
      return <TypeName>dict</TypeName>;
    } else if (this.props.type.typeAttributes.isNamed) {
      return (
        <Link
          to={{
            search: `?typeExplorer=${this.props.type.name}`
          }}
        >
          <TypeName>{this.props.type.name}</TypeName>
        </Link>
      );
    } else {
      return <TypeName>{this.props.type.name}</TypeName>;
    }
  }
}

export const TypeName = styled.code`
  background: #d6ecff;
  border: none;
  padding: 1px 4px;
  border-bottom: 1px solid #2491eb;
  border-radius: 0.25em;
  font-weight: 500;
`;
