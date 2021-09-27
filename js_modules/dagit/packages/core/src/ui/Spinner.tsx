// eslint-disable-next-line no-restricted-imports
import {Spinner as BlueprintSpinner} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP} from './Colors';

type SpinnerPurpose = 'page' | 'section' | 'body-text' | 'caption-text';

export const Spinner: React.FC<{
  purpose: SpinnerPurpose;
  value?: number;
  fillColor?: string;
}> = ({purpose, value, fillColor = ColorsWIP.Gray600}) => {
  const size = () => {
    switch (purpose) {
      case 'page':
        return 80;
      case 'section':
        return 32;
      case 'caption-text':
        return 10;
      case 'body-text':
      default:
        return 12;
    }
  };

  const padding = () => {
    switch (purpose) {
      case 'caption-text':
        return 1;
      case 'body-text':
        return 2;
      default:
        return 0;
    }
  };

  return (
    <SpinnerWrapper $padding={padding()}>
      <SlowSpinner size={size()} value={value} $fillColor={fillColor} />
    </SpinnerWrapper>
  );
};

export const SpinnerWrapper = styled.div<{$padding: number}>`
  padding: ${({$padding}) => $padding}px;
`;

const SlowSpinner = styled(BlueprintSpinner)<{$fillColor: string}>`
  .bp3-spinner-animation {
    animation-duration: 0.8s;

    path.bp3-spinner-track {
      stroke: ${(p) => p.$fillColor};
      stroke-opacity: 0.25;
    }
    path.bp3-spinner-head {
      stroke: ${(p) => p.$fillColor};
      stroke-opacity: 1;
    }
  }
`;
