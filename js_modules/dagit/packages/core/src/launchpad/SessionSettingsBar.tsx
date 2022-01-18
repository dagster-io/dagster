import {ColorsWIP} from '@dagster-io/ui';
import styled from 'styled-components/macro';

export const SessionSettingsBar = styled.div`
  color: white;
  display: flex;
  position: relative;
  border-bottom: 1px solid ${ColorsWIP.Gray200};
  background: ${ColorsWIP.White};
  align-items: center;
  height: 47px;
  padding: 8px 10px;
`;
