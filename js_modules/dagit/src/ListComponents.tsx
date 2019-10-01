import { Colors } from "@blueprintjs/core";
import styled from "styled-components";

export const Header = styled.div`
  color: ${Colors.BLACK};
  font-size: 1.1rem;
  line-height: 3rem;
  margin-top: 40px;
`;

export const Legend = styled.div`
  display: flex;
  padding: 2px 10px;
  text-decoration: none;
`;
export const LegendColumn = styled.div`
  flex: 1;
  color: #8a9ba8;
  padding: 7px 10px;
  text-transform: uppercase;
  font-size: 11px;
`;

export const RowContainer = styled.div`
  display: flex;
  background: ${Colors.WHITE};
  color: ${Colors.DARK_GRAY5};
  border-bottom: 1px solid ${Colors.LIGHT_GRAY1};
  margin-bottom: 9px;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
  padding: 2px 10px;
  text-decoration: none;
`;
export const RowColumn = styled.div`
  flex: 1;
  padding: 7px 10px;
  border-right: 1px solid ${Colors.LIGHT_GRAY3};
  &:last-child {
    border-right: none;
  }
`;
export const ScrollContainer = styled.div`
  background-color: rgb(245, 248, 250);
  padding: 20px;
  overflow: auto;
  min-height: calc(100vh - 50px);
`;
export const Details = styled.div`
  font-size: 0.8rem;
  margin-top: 4px;
`;
