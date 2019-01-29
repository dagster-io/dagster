import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Link } from "react-router-dom";

interface ITypeWithTooltipProps {
  type: {
    name: string | null;
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
        description
      }
    `
  };

  render() {
    const { name } = this.props.type;
    const search = `?typeExplorer=${name}`;

    return (
      <Link to={{ search }}>
        <TypeName>{name || "Unnamed Type"}</TypeName>
      </Link>
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
