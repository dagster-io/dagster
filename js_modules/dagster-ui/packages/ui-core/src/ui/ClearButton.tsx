import styled from 'styled-components';

import {
  IconWrapper,
  colorAccentGray,
  colorAccentGrayHover,
  colorTextDefault,
} from '@dagster-io/ui-components';

export const ClearButton = styled.button`
  background: transparent;
  border: none;
  cursor: pointer;
  margin: 0 -2px 0 0;
  padding: 2px;

  ${IconWrapper} {
    background-color: ${colorAccentGray()};
    transition: background-color 100ms linear;
  }

  :hover ${IconWrapper}, :focus ${IconWrapper} {
    background-color: ${colorAccentGrayHover()};
  }

  :active ${IconWrapper} {
    background-color: ${colorTextDefault()};
  }

  :focus {
    outline: none;
  }
`;
