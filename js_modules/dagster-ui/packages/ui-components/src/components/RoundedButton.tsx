import styled from 'styled-components';

import {Colors} from './Color';
import {IconWrapper} from './Icon';

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
  padding: 0 8px 0 4px;
  user-select: none;

  &:focus,
  &:active {
    outline: none;
  }

  ${IconWrapper} {
    background: ${Colors.navText()};
  }

  &:hover {
    background-color: ${Colors.navButtonHover()};

    ${IconWrapper} {
      background: ${Colors.navTextSelected()};
    }
  }

  ${IconWrapper} {
    transition: linear 100ms background;
  }
`;
