// eslint-disable-next-line no-restricted-imports
import {Spinner as BlueprintSpinner} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

import {colorAccentGray} from '../theme/color';
import { Icon } from './Icon';

interface Props {
  fillColor?: string;
  stopped?: boolean;
}

export const AnimatedAutomatorIcon = ({
  fillColor = colorAccentGray(),
  stopped = true,
}: Props) => {
  return (
    <IconWrapper 
      $stopped={stopped}
    >
      <Icon name="sensors" color={fillColor} />
    </IconWrapper>
  );
};


const IconWrapper = styled.div<{$stopped?: boolean}>`
  @keyframes rotate {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
  }

  {
    ${(p) => (!p.$stopped && 'animation: rotate 8s linear infinite;')}
    width: 16px;
    height: 16px;
    display: flex;
    justify-content: center;
    align-items: center;
    margin-right: 4px;
  }
`;
