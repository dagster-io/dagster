import styled from 'styled-components';

import {
  colorAccentReversed,
  colorBackgroundDefault,
  colorBorderDefault,
} from '@dagster-io/ui-components';

export const SessionSettingsBar = styled.div`
  color: ${colorAccentReversed()};
  display: flex;
  position: relative;
  border-bottom: 1px solid ${colorBorderDefault()};
  background: ${colorBackgroundDefault()};
  align-items: center;
  height: 47px;
  padding: 8px 10px;
`;
