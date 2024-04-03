import {Colors, IconWrapper, UnstyledButton} from '@dagster-io/ui-components';
import styled from 'styled-components';

export const TopNavButton = styled(UnstyledButton)`
  background-color: ${Colors.navButton()};
  height: 32px;
  width: 32px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;

  :hover,
  :focus {
    background-color: ${Colors.navButtonHover()};
  }

  :focus:not(:active) {
    outline: ${Colors.focusRing()} auto 1px;
  }

  ${IconWrapper} {
    background-color: ${Colors.accentWhite()};
    transition: background-color 100ms linear;
  }

  :focus ${IconWrapper}, :hover ${IconWrapper} {
    background-color: ${Colors.navTextHover()};
  }
`;
