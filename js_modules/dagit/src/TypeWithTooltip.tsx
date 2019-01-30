import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Link } from "react-router-dom";

interface ITypeWithTooltipProps {
  type: {
    name: string | null;
    displayName: string;
    description: string | null;
  };
}

export default class TypeWithTooltip extends React.Component<
  ITypeWithTooltipProps
> {
  static fragments = {
    RuntimeTypeWithTooltipFragment: gql`
      fragment RuntimeTypeWithTooltipFragment on RuntimeType {
        name
        displayName
        description
      }
    `
  };

  render() {
    const { name, displayName } = this.props.type;
    const search = `?typeExplorer=${displayName}`;

    // TODO: link to most inner type
    return name ? (
      <Link to={{ search }}>
        <TypeName>{displayName}</TypeName>
      </Link>
    ) : (
      <TypeName>{displayName}</TypeName>
    );
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
