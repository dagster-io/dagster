import styled from 'styled-components';

import {Colors} from './Color';
import {FontFamily} from './styles';

interface TextProps {
  color?: string;
}

const Text = styled.span<TextProps>`
  ${({color}) => (color ? `color: ${color};` : null)}
`;

export const Title = styled(Text)`
  font-size: 32px;
  line-height: 36px;
  font-weight: 600;
  -webkit-font-smoothing: antialiased;
`;

export const Heading = styled(Text)`
  font-size: 20px;
  line-height: 24px;
  font-weight: 500;
  -webkit-font-smoothing: antialiased;
`;

export const SubtitleLarge = styled(Text)`
  font-size: 16px;
  line-height: 20px;
  font-weight: 500;
  -webkit-font-smoothing: antialiased;
`;

export const Subtitle = styled(Text)`
  font-size: 14px;
  line-height: 20px;
  font-weight: 500;
  -webkit-font-smoothing: antialiased;
`;

export const SubtitleSmall = styled(Text)`
  font-size: 12px;
  line-height: 16px;
  font-weight: 500;
`;

export const BodyLarge = styled(Text)`
  font-size: 16px;
  line-height: 20px;
  font-weight: 400;
`;

export const Body = styled(Text)`
  font-family: ${FontFamily.default};
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
`;

export const BodySmall = styled(Text)`
  font-family: ${FontFamily.default};
  font-size: 12px;
  line-height: 16px;
  font-weight: 400;
`;

export const MonoLarge = styled(Text)`
  font-family: ${FontFamily.monospace};
  font-size: 16px;
  line-height: 20px;
  font-weight: 400;
`;

export const Mono = styled(Text)`
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
`;

export const MonoSmall = styled(Text)`
  font-family: ${FontFamily.monospace};
  font-size: 12px;
  line-height: 16px;
  font-weight: 400;
`;

export const Code = styled(Text)`
  background-color: ${Colors.backgroundBlue()};
  border-radius: 2px;
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  padding: 2px 4px;
`;

//Depricated – Use BodySmall moving forward
export const Caption = styled(Text)`
  font-family: ${FontFamily.default};
  font-size: 12px;
`;
