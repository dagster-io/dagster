import {Spinner} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

export const LoadingOverlay: React.FC<{
  isLoading: boolean;
  message: string;
}> = ({isLoading, message}) => (
  <LoadingOverlayContainer isLoading={isLoading}>
    <Spinner size={24} />
    &nbsp;&nbsp;{message}
  </LoadingOverlayContainer>
);

const LoadingOverlayContainer = styled.div<{isLoading: boolean}>`
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  background-color: #fff;
  z-index: 20;
  display: ${({isLoading}) => (!isLoading ? 'none' : 'flex')};
  align-items: center;
  justify-content: center;
  opacity: ${({isLoading}) => (isLoading ? '0.7' : '0')};
  transition: opacity 150ms linear;
  transition-delay: 300ms;
`;
