import styled from 'styled-components';

import {Colors} from './Color';

export const Skeleton = styled.div<{$height?: string | number; $width?: string | number}>`
  width: ${(p) => (Number(p.$width) ? `${p.$width}px` : p.$width ? p.$width : `100%`)};
  height: ${(p) => (Number(p.$height) ? `${p.$height}px` : p.$height ? p.$height : `100%`)};
  display: block;
  min-height: 1.5em;
  border-radius: 6px;
  background: ${Colors.backgroundLight()};
  position: relative;
  overflow: hidden;

  &::after {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    background: linear-gradient(
      90deg,
      ${Colors.backgroundLight()} 0%,
      ${Colors.backgroundLightHover()} 50%,
      ${Colors.backgroundLight()} 100%
    );
    animation: skeleton-loading 1.4s ease infinite;
  }

  @keyframes skeleton-loading {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(100%);
    }
  }
`;
