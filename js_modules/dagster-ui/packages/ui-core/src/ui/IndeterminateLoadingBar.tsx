import {Colors} from '@dagster-io/ui-components';
import styled from 'styled-components';

export const IndeterminateLoadingBar = styled.div<{$loading?: boolean}>`
  height: 2px;
  width: 100%;
  flex-shrink: 0;
  background: ${Colors.backgroundGray()};
  border-radius: 0 0 8px 8px;
  overflow: hidden;

  ${({$loading}) =>
    $loading
      ? `
  &::after {
    content: '';
    display: block;
    height: 100%;
    width: 100%;
    background: ${Colors.accentBlue()};
    transform-origin: left center;
    will-change: transform;
    animation: load 2s infinite;
    contain: layout style size;
    isolation: isolate;

    @keyframes load {
      0% {
        transform: scaleX(0);
      }
      50% {
        transform: scaleX(0.5);
      }
      100% {
        transform: scaleX(1);
      }
    }
  }
    `
      : ''}
`;
