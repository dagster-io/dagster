import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Link } from "react-router-dom";
import { Code, Position, Tooltip, Text } from "@blueprintjs/core";
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
      }
    `
  };

  render() {
    if (true || this.props.link) {
      return (
        <Link
          to={{
            search: `?typeExplorer=${this.props.type.name}`
          }}
        >
          <TypeName>{this.props.type.name}</TypeName>
        </Link>
      );
    }
    //   } else if (
    //     this.props.type.description &&
    //     this.props.type.description.length > 0
    //   ) {
    //     return (
    //       <Tooltip
    //         content={
    //           <TypeDescription>{this.props.type.description}</TypeDescription>
    //         }
    //       >
    //         <TypeNameWithHelp>{this.props.type.name}</TypeNameWithHelp>
    //       </Tooltip>
    //     );
    //   } else {
    //     return <TypeName>{this.props.type.name}</TypeName>;
    //   }
  }
}

const TypeName = styled.code`
  background: #d6ecff;
  border: none;
  padding: 1px 4px;
  border-bottom: 1px solid #2491eb;
  border-radius: 0.25em;
  font-weight: 500;
`;

const TypeNameWithHelp = styled(TypeName)`
  cursor: help;
`;

const TypeDescription = styled(Text)`
  max-width: 300px;
`;
