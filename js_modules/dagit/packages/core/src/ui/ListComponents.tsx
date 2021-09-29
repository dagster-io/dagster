import styled from 'styled-components/macro';

import {ColorsWIP} from './Colors';

export const RowContainer = styled.div`
  display: flex;
  color: ${ColorsWIP.Gray700};
  margin-bottom: 9px;
  border: 1px solid ${ColorsWIP.Gray200};
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
  padding: 2px 10px;
  text-decoration: none;
`;

export const ScrollContainer = styled.div`
  overflow: auto;
  width: 100%;
`;
