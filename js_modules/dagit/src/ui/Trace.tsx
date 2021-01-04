import {Colors} from '@blueprintjs/core';
import styled from 'styled-components';

import {FontFamily} from 'src/ui/styles';

export const Trace = styled.div`
  background-color: ${Colors.LIGHT_GRAY1};
  color: rgb(41, 50, 56);
  font-family: ${FontFamily.monospace};
  font-size: 12px;
  max-height: 90vh;
  overflow: auto;
  white-space: pre;
  padding: 16px;
`;
