import styled from 'styled-components';

import {Colors} from './Color';

export const Skeleton = styled.div<{$height?: string | number; $width?: string | number}>`
  width: ${(p) => (Number(p.$width) ? `${p.$width}px` : p.$width ? p.$width : `100%`)};
  height: ${(p) => (Number(p.$height) ? `${p.$height}px` : p.$height ? p.$height : `100%`)};
  display: block;
  min-height: 1.5em;
  border-radius: 6px;
  background: linear-gradient(
    90deg,
    ${Colors.backgroundLight()} 25%,
    ${Colors.backgroundLightHover()} 37%,
    ${Colors.backgroundLight()} 63%
  );
  background-size: 400% 100%;
  animation-name: skeleton-loading;
  animation-duration: 1.4s;
  animation-timing-function: ease;
  animation-iteration-count: infinite;

  @keyframes skeleton-loading {
    0% {
      background-position: 100% 50%;
    }
    100% {
      background-position: 0 50%;
    }
  }
`;
