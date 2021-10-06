import styled from 'styled-components/macro';

import {ColorsWIP} from './Colors';
import {FontFamily} from './styles';

interface TextProps {
  color?: string;
}

export const Heading = styled.span<TextProps>`
  font-size: 18px;
  font-weight: 600;
  line-height: 24px;
  -webkit-font-smoothing: antialiased;
`;

export const Subheading = styled.span<TextProps>`
  font-size: 14px;
  font-weight: 600;
  line-height: 20px;
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
  background-color: ${ColorsWIP.Gray100};
  border-radius: 3px;
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  padding: 2px 4px;
`;

export const Mono = styled.span`
  font-family: ${FontFamily.monospace};
  font-size: 16px;
`;
