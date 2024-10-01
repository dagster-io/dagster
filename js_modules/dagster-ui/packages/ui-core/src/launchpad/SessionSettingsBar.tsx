import {Colors} from '@dagster-io/ui-components';
import styled from 'styled-components';

export const SessionSettingsBar = styled.div`
  color: ${Colors.accentReversed()};
  display: flex;
  position: relative;
  border-bottom: 1px solid ${Colors.borderDefault()};
  background: ${Colors.backgroundDefault()};
  align-items: center;
  height: 47px;
  padding: 8px 10px;
`;
