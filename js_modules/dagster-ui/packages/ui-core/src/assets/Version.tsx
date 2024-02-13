import {FontFamily} from '@dagster-io/ui-components';
import styled from 'styled-components';

export const Version = styled.div`
  font-family: ${FontFamily.monospace};
  font-size: 16px;
  overflow: hidden;
  text-overflow: ellipsis;
`;
