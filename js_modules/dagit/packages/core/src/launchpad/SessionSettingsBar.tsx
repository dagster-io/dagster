import {Colors} from '@dagster-io/ui';
import styled from 'styled-components/macro';

export const SessionSettingsBar = styled.div`
  color: white;
  display: flex;
  position: relative;
  border-bottom: 1px solid ${Colors.Gray200};
  background: ${Colors.White};
  align-items: center;
  height: 47px;
  padding: 8px 10px;
`;
