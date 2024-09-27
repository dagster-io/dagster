import {Colors} from '@dagster-io/ui-components';
import styled from 'styled-components';

export const IndeterminateLoadingBar = styled.div<{loading?: boolean}>`
  height: 2px;
  width: 100%;
  background: ${Colors.backgroundGray()};
  border-radius: 0 0 8px 8px;
  overflow: hidden;

  ${({loading}) =>
    loading
      ? `
  &::after {
    content: '';
    display: block;
    height: 100%;
    width: 0%;
    background: ${Colors.accentBlue()};
    animation: load 2s infinite;

    @keyframes load {
      0% {
        width: 0%;
      }
      50% {
        width: 50%;
      }
      100% {
        width: 100%;
      }
    }
  }
    `
      : ''}
`;
