import styled from 'styled-components';

export const InsightsIdentifierDot = styled.div<{$color: string}>`
  background-color: ${({$color}) => $color};
  border-radius: 50%;
  height: 12px;
  width: 12px;
  flex-shrink: 0;
  cursor: pointer;
`;
