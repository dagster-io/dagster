import * as React from 'react';
import styled from 'styled-components/macro';

import {TagWIP} from './TagWIP';

interface ITagProps {
  tag: {
    key: string;
    value: string;
  };
  onClick?: (tag: {key: string; value: string}) => void;
  isDagsterTag?: boolean;
}

export const Tag = ({tag, onClick, isDagsterTag}: ITagProps) => {
  const onTagClick = () => onClick && onClick(tag);

  return (
    <TagButton onClick={onTagClick}>
      <TagWIP intent={isDagsterTag ? 'none' : 'primary'} interactive>
        {tag.key}: {tag.value}
      </TagWIP>
    </TagButton>
  );
};

const TagButton = styled.button`
  border: none;
  background: none;
  padding: 0;
  margin: 0;
  text-align: left;

  :focus {
    outline: none;
  }
`;
