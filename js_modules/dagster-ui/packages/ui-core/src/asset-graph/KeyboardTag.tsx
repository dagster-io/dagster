import {Colors} from '@dagster-io/ui-components';
import styled from 'styled-components';

interface KeyboardTagProps {
  $withinTooltip?: boolean;
}

export const KeyboardTag = styled.div<KeyboardTagProps>`
  ${(props) => {
    return props.$withinTooltip ? `color: ${Colors.accentWhite()}` : `color: ${Colors.textLight()}`;
  }};
  background: ${Colors.backgroundGray()};
  border-radius: 4px;
  padding: 2px 4px;
  margin-left: 6px;
  font-size: 12px;
`;
