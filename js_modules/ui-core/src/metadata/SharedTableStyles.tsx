import {Colors} from '@dagster-io/ui-components';
import styled from 'styled-components';

export const StyledTableWithHeader = styled.table`
  /** -2 accounts for the left and right border, which are not taken into account
   * and cause a tiny amount of horizontal scrolling at all times. */
  width: calc(100% - 2px);
  border-spacing: 0;
  border-collapse: collapse;

  & > thead > tr > td {
    color: ${Colors.textLighter()};
    font-size: 12px;
    line-height: 16px;
  }

  & > tbody > tr > td,
  & > thead > tr > td {
    border: 1px solid ${Colors.keylineDefault()};
    padding: 8px 12px;
    font-size: 14px;
    line-height: 20px;
    vertical-align: top;

    &:first-child {
      max-width: 300px;
      word-wrap: break-word;
      width: 25%;
    }
  }
`;
