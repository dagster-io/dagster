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
  font-size: 24px;
  font-weight: 600;
  line-height: 30px;
  -webkit-font-smoothing: antialiased;
`;

export const Heading = styled(Text)`
  font-size: 18px;
  font-weight: 600;
  line-height: 24px;
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

export const Caption = styled(Text)`
  font-family: ${FontFamily.default};
  font-size: 12px;
`;

export const CaptionSubtitle = styled(Text)`
  font-size: 12px;
  font-weight: 600;
  line-height: 16px;
`;

export const CaptionBolded = styled(Text)`
  font-family: ${FontFamily.default};
  font-size: 12px;
  font-weight: 900;
`;

export const Code = styled(Text)`
  background-color: ${Colors.backgroundBlue()};
  border-radius: 2px;
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  padding: 2px 4px;
`;

export const Mono = styled(Text)`
  font-family: ${FontFamily.monospace};
  font-size: 16px;
`;

export const CaptionMono = styled(Text)`
  font-family: ${FontFamily.monospace};
  font-size: 14px;
`;
