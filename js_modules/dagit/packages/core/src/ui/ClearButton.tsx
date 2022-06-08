import {Colors, IconWrapper} from '@dagster-io/ui';
import styled from 'styled-components/macro';

export const ClearButton = styled.button`
  background: transparent;
  border: none;
  cursor: pointer;
  margin: 0 -2px 0 0;
  padding: 2px;

  ${IconWrapper} {
    background-color: ${Colors.Gray400};
    transition: background-color 100ms linear;
  }

  :hover ${IconWrapper}, :focus ${IconWrapper} {
    background-color: ${Colors.Gray700};
  }

  :active ${IconWrapper} {
    background-color: ${Colors.Dark};
  }

  :focus {
    outline: none;
  }
`;
