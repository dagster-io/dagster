import {Box, Colors, FontFamily, IconWrapper, UnstyledButton} from '@dagster-io/ui-components';
import {ReactNode} from 'react';
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

interface TooltipWithShortcutInfoProps {
  label: ReactNode;
  shortcutKey: string;
}

export const TooltipShortcutInfo = ({label, shortcutKey}: TooltipWithShortcutInfoProps) => {
  return (
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
      <div>{label}</div>
      <TooltipShortcutKey>{shortcutKey}</TooltipShortcutKey>
    </Box>
  );
};

export const TooltipShortcutKey = styled.div`
  background-color: ${Colors.navButton()};
  border-radius: 3px;
  font-family: ${FontFamily.monospace};
  padding: 1px 6px;
  box-shadow: inset 0 0 0 1px ${Colors.borderHover()};
`;
