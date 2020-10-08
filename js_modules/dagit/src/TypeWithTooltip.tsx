import gql from 'graphql-tag';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

interface ITypeWithTooltipProps {
  type: {
    name: string | null;
    displayName: string;
    description: string | null;
  };
}

export class TypeWithTooltip extends React.Component<ITypeWithTooltipProps> {
  static fragments = {
    DagsterTypeWithTooltipFragment: gql`
      fragment DagsterTypeWithTooltipFragment on DagsterType {
        name
        displayName
        description
      }
    `,
  };

  render() {
    const {name, displayName} = this.props.type;

    // TODO: link to most inner type
    if (name) {
      const search = `?typeExplorer=${displayName}`;
      return (
        <Link to={{search}}>
          <TypeName>{displayName}</TypeName>
        </Link>
      );
    } else {
      return <TypeName>{displayName}</TypeName>;
    }
  }
}

export const TypeName = styled.code`
  background: #d6ecff;
  border: none;
  padding: 1px 4px;
  border-bottom: 1px solid #2491eb;
  border-radius: 0.25em;
  font-size: 12px;
  font-weight: 500;
`;
