// eslint-disable-next-line no-restricted-imports
import {Spinner as BlueprintSpinner} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

type SpinnerPurpose = 'page' | 'section' | 'body-text' | 'caption-text';

export const Spinner: React.FC<{
  purpose: SpinnerPurpose;
  value?: number;
}> = ({purpose, value}) => {
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

  return <SlowSpinner size={size()} value={value} />;
};

const SlowSpinner = styled(BlueprintSpinner)`
  .bp3-spinner-animation {
    animation-duration: 0.8s;
  }
`;
