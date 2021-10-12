import styled from 'styled-components/macro';

import {ColorsWIP} from './Colors';

export const RowContainer = styled.div`
  display: flex;
  box-sizing: border-box;
  color: ${ColorsWIP.Gray700};
  border-left: 1px solid ${ColorsWIP.KeylineGray};
  border-bottom: 1px solid ${ColorsWIP.KeylineGray};
  padding: 24px 12px;
  text-decoration: none;
`;
