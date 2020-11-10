import {Colors} from '@blueprintjs/core';
import styled from 'styled-components';

import {FontFamily} from 'src/ui/styles';

interface TextProps {
  color?: string;
}

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
  background-color: ${Colors.LIGHT_GRAY3};
  border-radius: 3px;
  font-family: ${FontFamily.monospace};
  font-size: 13px;
  padding: 1px 4px;
`;
