import {gql} from '@apollo/client';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {useActiveRepo} from 'src/workspace/WorkspaceContext';

interface ITypeWithTooltipProps {
  type: {
    name: string | null;
    displayName: string;
    description: string | null;
  };
}

export const TypeWithTooltip = (props: ITypeWithTooltipProps) => {
  const activeRepo = useActiveRepo();
  const {name, displayName} = props.type;

  // TODO: link to most inner type
  if (name && activeRepo) {
    return (
      <Link to={{search: `?typeExplorer=${displayName}`}}>
        <TypeName>{displayName}</TypeName>
      </Link>
    );
  }

  return <TypeName>{displayName}</TypeName>;
};

TypeWithTooltip.fragments = {
  DagsterTypeWithTooltipFragment: gql`
    fragment DagsterTypeWithTooltipFragment on DagsterType {
      name
      displayName
      description
    }
  `,
};

const TypeName = styled.code`
  background: #d6ecff;
  border: none;
  padding: 1px 4px;
  border-bottom: 1px solid #2491eb;
  border-radius: 0.25em;
  font-size: 12px;
  font-weight: 500;
`;
