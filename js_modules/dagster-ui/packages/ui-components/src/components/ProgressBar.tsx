// eslint-disable-next-line no-restricted-imports
import * as React from 'react';
import {ProgressBar as BlueprintProgressBar, ProgressBarProps} from '@blueprintjs/core';
import styled from 'styled-components';

import {colorAccentGray} from '../theme/color';

interface Props extends ProgressBarProps {
  fillColor?: string;
}

export const ProgressBar = ({fillColor = colorAccentGray(), ...rest}: Props) => {
  return (
    <StyledProgressBar
      {...rest}
      intent="none"
      $fillColor={fillColor}
      stripes={rest.animate ? true : false}
    />
  );
};

const StyledProgressBar = styled(BlueprintProgressBar)<{$fillColor: string}>`
  &.bp4-progress-bar {
    background: transparent;

    ::before {
      content: '';
      background: ${(p) => p.$fillColor};
      position: absolute;
      inset: 0;
      opacity: 0.25;
    }

    .bp4-progress-meter {
      background-color: ${(p) => p.$fillColor};
    }
  }
`;
