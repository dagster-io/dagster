import {Colors} from '@dagster-io/ui-components';
import styled from 'styled-components';

export const ClearButton = styled.button`
  background: transparent;
  border: none;
  cursor: pointer;
  margin: 0 -2px 0 0;
  padding: 2px;

  .iconGlobal {
    background-color: ${Colors.accentGray()};
    transition: background-color 100ms linear;
  }

  :hover .iconGlobal,
  :focus .iconGlobal {
    background-color: ${Colors.accentGrayHover()};
  }

  :active .iconGlobal {
    background-color: ${Colors.textDefault()};
  }

  :focus {
    outline: none;
  }
`;
