import * as React from 'react';
import styled from 'styled-components/macro';

export const AnimatedEllipsis = () => {
  return (
    <AnimatedEllipsisContainer>
      <span>.</span>
      <span>.</span>
      <span>.</span>
    </AnimatedEllipsisContainer>
  );
};

const AnimatedEllipsisContainer = styled.span`
  @keyframes ellipsis-dot {
    0% {
      opacity: 0;
    }
    50% {
      opacity: 1;
    }
    100% {
      opacity: 0;
    }
  }
  span {
    opacity: 0;
    animation: ellipsis-dot 1s infinite;
  }
  span:nth-child(1) {
    animation-delay: 0s;
  }
  span:nth-child(2) {
    animation-delay: 0.1s;
  }
  span:nth-child(3) {
    animation-delay: 0.2s;
  }
`;
