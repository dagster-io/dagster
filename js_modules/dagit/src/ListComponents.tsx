import {Colors} from '@blueprintjs/core';
import styled from 'styled-components/macro';

export const Header = styled.div`
  color: ${Colors.BLACK};
  font-size: 1.1rem;
  margin-bottom: 10px;
`;

export const RowContainer = styled.div`
  display: flex;
  color: ${Colors.DARK_GRAY5};
  margin-bottom: 9px;
  border: 1px solid ${Colors.LIGHT_GRAY1};
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
  padding: 2px 10px;
  text-decoration: none;
`;

export const ScrollContainer = styled.div`
  overflow: auto;
  width: 100%;
`;
