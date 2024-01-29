import styled from 'styled-components';

import {Colors} from './Color';
import {FontFamily} from './styles';

export const Trace = styled.div`
  background-color: ${Colors.backgroundLight()};
  color: ${Colors.textLight()};
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  max-height: 90vh;
  overflow: auto;
  white-space: pre;
  padding: 16px;
`;
