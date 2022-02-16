import * as React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP, IconWIP} from '..';

export const Warning: React.FC<{errorBackground?: boolean}> = ({errorBackground, children}) => {
  return (
    <ErrorContainer errorBackground={errorBackground}>
      <IconWIP name="warning" size={16} color={ColorsWIP.Gray700} style={{marginRight: 8}} />
      {children}
    </ErrorContainer>
  );
};

const ErrorContainer = styled.div<{errorBackground?: boolean}>`
  border-top: 1px solid ${ColorsWIP.KeylineGray};
  background: ${({errorBackground}) => (errorBackground ? ColorsWIP.Red100 : ColorsWIP.Gray50)};
  padding: 8px 24px 8px 24px;
  display: flex;
  align-items: center;
  font-size: 12px;
`;
