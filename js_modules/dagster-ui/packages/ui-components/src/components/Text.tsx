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

export const Headline = styled(Text)`
  font-size: 18px;
  font-weight: 500;
  line-height: 24px;
  -webkit-font-smoothing: antialiased;
`;

export const Subheading = styled(Text)`
  font-size: 14px;
  font-weight: 600;
  line-height: 20px;
  -webkit-font-smoothing: antialiased;
`;

export const Subtitle1 = styled(Text)`
  font-size: 16px;
  font-weight: 600;
  line-height: 24px;
  -webkit-font-smoothing: antialiased;
`;

export const Subtitle2 = styled(Text)`
  font-size: 14px;
  font-weight: 600;
  line-height: 20px;
  -webkit-font-smoothing: antialiased;
`;

export const Body = styled(Text)`
  font-family: ${FontFamily.default};
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
`;

export const Body1 = styled(Text)`
  font-size: 16px;
  font-weight: 400;
  line-height: 24px;
`;

export const Body2 = styled(Text)`
  font-family: ${FontFamily.default};
  line-height: 20px;
  font-size: 14px;
  font-weight: 400;
`;

//Deprecated – Use BodySmall moving forward
export const Caption = styled(Text)`
  font-family: ${FontFamily.default};
  font-size: 12px;
  line-height: 16px;
`;

export const CaptionSubtitle = styled(Text)`
  font-size: 12px;
  font-weight: 600;
  line-height: 16px;
`;

export const CaptionBolded = styled(Text)`
  font-family: ${FontFamily.default};
  font-size: 12px;
  font-weight: 700;
  line-height: 16px;
`;

export const Code = styled(Text)`
  background-color: ${Colors.backgroundBlue()};
  border-radius: 2px;
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  font-variant-ligatures: none;
  padding: 2px 4px;
`;

export const Mono = styled(Text)`
  font-family: ${FontFamily.monospace};
  font-variant-ligatures: none;
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
`;

export const CaptionMono = styled(Text)`
  font-family: ${FontFamily.monospace};
  font-variant-ligatures: none;
  font-size: 12px;
  line-height: 16px;
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

export const MonoSmall = styled(Text)`
  font-family: ${FontFamily.monospace};
  font-size: 12px;
  line-height: 16px;
  font-weight: 400;
`;
