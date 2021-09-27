// eslint-disable-next-line no-restricted-imports
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

// interface TagChildProps {
//   isDagsterTag?: boolean;
// }

// const TagElement = styled(({isDagsterTag, ...rest}) => <TagWIP {...rest} />)<TagChildProps>`
//   padding: 1px !important;
//   margin: 1px 2px !important;
//   overflow: hidden;
//   background-color: ${({isDagsterTag}) => (isDagsterTag ? Colors.LIGHT_GRAY2 : Colors.GRAY1)};
//   border: ${({isDagsterTag}) =>
//     isDagsterTag ? `1px solid ${Colors.LIGHT_GRAY1}` : `1px solid ${Colors.GRAY1}`};
//   color: ${({isDagsterTag}) => (isDagsterTag ? Colors.DARK_GRAY1 : Colors.WHITE)};
//   cursor: ${({onClick}) => (onClick ? `pointer` : 'default')};
//   max-width: 400px;
// `;

// const TagKey = styled.span`
//   padding: 2px 4px;
// `;

// const TagValue = styled.span<TagChildProps>`
//   background-color: ${({isDagsterTag}) => (isDagsterTag ? Colors.LIGHT_GRAY4 : Colors.GRAY3)};
//   border-radius: 3px;
//   padding: 2px 4px;
// `;
