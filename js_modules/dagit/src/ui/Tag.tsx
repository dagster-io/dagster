import {Colors, Tag as BlueprintTag} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

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
    <TagElement isDagsterTag={isDagsterTag} onClick={onTagClick}>
      <TagKey>{tag.key}</TagKey>
      <TagValue isDagsterTag={isDagsterTag}>{tag.value}</TagValue>
    </TagElement>
  );
};

interface TagChildProps {
  isDagsterTag?: boolean;
}

const TagElement = styled(({isDagsterTag, ...rest}) => <BlueprintTag {...rest} />)<TagChildProps>`
  padding: 1px !important;
  margin: 1px 2px !important;
  overflow: hidden;
  background-color: ${({isDagsterTag}) => (isDagsterTag ? Colors.LIGHT_GRAY2 : Colors.GRAY1)};
  border: ${({isDagsterTag}) =>
    isDagsterTag ? `1px solid ${Colors.LIGHT_GRAY1}` : `1px solid ${Colors.GRAY1}`};
  color: ${({isDagsterTag}) => (isDagsterTag ? Colors.DARK_GRAY1 : Colors.WHITE)};
  cursor: ${({onClick}) => (onClick ? `pointer` : 'default')};
  max-width: 400px;
`;

const TagKey = styled.span`
  padding: 2px 4px;
`;

const TagValue = styled.span<TagChildProps>`
  background-color: ${({isDagsterTag}) => (isDagsterTag ? Colors.LIGHT_GRAY4 : Colors.GRAY3)};
  border-radius: 3px;
  padding: 2px 4px;
`;
