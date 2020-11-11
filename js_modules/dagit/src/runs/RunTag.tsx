import {Colors, Position, Tag, Tooltip} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

export const DAGSTER_TAG_NAMESPACE = 'dagster/';

interface IRunTagProps {
  tag: {
    key: string;
    value: string;
  };
  onClick?: (tag: {key: string; value: string}) => void;
}

export const RunTag = ({tag, onClick}: IRunTagProps) => {
  const onTagClick = onClick
    ? () => {
        onClick(tag);
      }
    : undefined;

  const isDagsterTag = tag.key.startsWith(DAGSTER_TAG_NAMESPACE);
  const tagKey = isDagsterTag ? tag.key.substr(DAGSTER_TAG_NAMESPACE.length) : tag.key;

  const tagContent = (
    <TagElement isDagsterTag={isDagsterTag} onClick={onTagClick}>
      <TagKey>{tagKey}</TagKey>
      <TagValue isDagsterTag={isDagsterTag}>{tag.value}</TagValue>
    </TagElement>
  );

  if (isDagsterTag) {
    return (
      <Tooltip
        content={`${tag.key}=${tag.value}`}
        wrapperTagName="div"
        targetTagName="div"
        position={Position.LEFT}
      >
        {tagContent}
      </Tooltip>
    );
  }

  return tagContent;
};

interface TagChildProps {
  isDagsterTag: boolean;
}

const TagElement = styled(({isDagsterTag, ...rest}) => <Tag {...rest} />)<TagChildProps>`
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
