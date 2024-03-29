import styled from 'styled-components';

import {Colors} from './Color';

export const RoundedButton = styled.button`
  background-color: ${Colors.navButton()};
  border-radius: 24px;
  border: 0;
  color: ${Colors.navTextSelected()};
  cursor: pointer;
  font-size: 14px;
  line-height: 20px;
  height: 32px;
  text-align: left;
  display: block;
  padding: 0 8px;
  user-select: none;

  &:focus,
  &:active {
    outline: none;
  }

  &:hover {
    background-color: ${Colors.navButtonHover()};
  }
`;
