import {gql} from '@apollo/client';
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

export const TypeWithTooltip = (props: ITypeWithTooltipProps) => {
  const {name, displayName} = props.type;

  // TODO: link to most inner type
  if (name) {
    return (
      <Link to={{search: `?tab=types&typeName=${displayName}`}}>
        <TypeName>{displayName}</TypeName>
      </Link>
    );
  }

  return <TypeName>{displayName}</TypeName>;
};

export const DAGSTER_TYPE_WITH_TOOLTIP_FRAGMENT = gql`
  fragment DagsterTypeWithTooltipFragment on DagsterType {
    name
    displayName
    description
  }
`;

const TypeName = styled.code`
  background: #d6ecff;
  border: none;
  padding: 1px 4px;
  border-bottom: 1px solid #2491eb;
  border-radius: 0.25em;
  font-size: 14px;
  font-weight: 500;
`;
