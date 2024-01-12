import {IconWrapper, Colors} from '@dagster-io/ui-components';
import styled from 'styled-components';

export const ClearButton = styled.button`
  background: transparent;
  border: none;
  cursor: pointer;
  margin: 0 -2px 0 0;
  padding: 2px;

  ${IconWrapper} {
    background-color: ${Colors.accentGray()};
    transition: background-color 100ms linear;
  }

  :hover ${IconWrapper}, :focus ${IconWrapper} {
    background-color: ${Colors.accentGrayHover()};
  }

  :active ${IconWrapper} {
    background-color: ${Colors.textDefault()};
  }

  :focus {
    outline: none;
  }
`;
