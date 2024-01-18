import styled from 'styled-components';

import {colorBackgroundLight, colorTextLight} from '../theme/color';
import {FontFamily} from './styles';

export const Trace = styled.div`
  background-color: ${colorBackgroundLight()};
  color: ${colorTextLight()};
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  max-height: 90vh;
  overflow: auto;
  white-space: pre;
  padding: 16px;
`;
