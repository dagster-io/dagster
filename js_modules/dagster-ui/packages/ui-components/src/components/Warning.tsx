import * as React from 'react';
import styled from 'styled-components';

import {
  colorAccentGray,
  colorBackgroundLight,
  colorBackgroundRed,
  colorKeylineDefault,
} from '../theme/color';

import {Icon} from './Icon';

interface Props {
  children: React.ReactNode;
  errorBackground?: boolean;
}

export const Warning = ({errorBackground, children}: Props) => {
  return (
    <ErrorContainer errorBackground={errorBackground}>
      <Icon name="warning" size={16} color={colorAccentGray()} style={{marginRight: 8}} />
      {children}
    </ErrorContainer>
  );
};

const ErrorContainer = styled.div<{errorBackground?: boolean}>`
  border-top: 1px solid ${colorKeylineDefault()};
  background: ${({errorBackground}) =>
    errorBackground ? colorBackgroundRed() : colorBackgroundLight()};
  padding: 8px 24px 8px 24px;
  display: flex;
  align-items: center;
  font-size: 12px;
`;
