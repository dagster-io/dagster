import {FontFamily} from '@dagster-io/ui';
import styled from 'styled-components/macro';

export const Version = styled.div`
  font-family: ${FontFamily.monospace};
  font-size: 16px;
  overflow: hidden;
  text-overflow: ellipsis;
`;
