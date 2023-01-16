import {gql} from '@apollo/client';
import {Colors} from '@dagster-io/ui';
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
      <TypeLink to={{search: `?tab=types&typeName=${displayName}`}}>
        <TypeName>{displayName}</TypeName>
      </TypeLink>
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

const TypeLink = styled(Link)`
  :hover {
    text-decoration: none;
  }
`;

const TypeName = styled.code`
  background: ${Colors.Blue50};
  border: none;
  padding: 1px 4px;
  border-bottom: 1px solid ${Colors.Blue500};
  border-radius: 0.25em;
  font-size: 14px;
  font-weight: 500;
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  vertical-align: middle;
`;
