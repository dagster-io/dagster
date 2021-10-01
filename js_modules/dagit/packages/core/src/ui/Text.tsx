import {Colors} from '@blueprintjs/core';
import styled from 'styled-components/macro';

import {FontFamily} from './styles';

interface TextProps {
  color?: string;
}

export const Heading = styled.span<TextProps>`
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
  -webkit-font-smoothing: antialiased;
`;

export const Subheading = styled.span<TextProps>`
  font-size: 20px;
  font-weight: 700;
  line-height: 1;
  -webkit-font-smoothing: antialiased;
`;

export const Body = styled.span<TextProps>`
  ${({color}) => (color ? `color: ${color};` : null)}
  font-family: ${FontFamily.default};
  font-size: 14px;
`;

export const Caption = styled.span<TextProps>`
  ${({color}) => (color ? `color: ${color};` : null)}
  font-family: ${FontFamily.default};
  font-size: 12px;
`;

export const Code = styled.span`
  background-color: ${Colors.LIGHT_GRAY4};
  border-radius: 3px;
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  padding: 2px 4px;
`;

export const Mono = styled.span`
  font-family: ${FontFamily.monospace};
  font-size: 16px;
`;
