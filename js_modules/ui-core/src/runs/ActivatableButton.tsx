import {Colors} from '@dagster-io/ui-components';
import styled, {css} from 'styled-components';

import {AnchorButton} from '../ui/AnchorButton';

export const ActivatableButton = styled(AnchorButton)<{$active: boolean}>`
  color: ${Colors.textLight()};

  &&:hover {
    color: ${Colors.textLight()};
  }

  ${({$active}) =>
    $active
      ? css`
          background-color: ${Colors.backgroundLighterHover()};
          color: ${Colors.textDefault()};

          &&:hover {
            background-color: ${Colors.backgroundLighterHover()};
            color: ${Colors.textDefault()};
          }
        `
      : css`
          background-color: ${Colors.backgroundDefault()};
        `}
`;
