import {Colors} from '@dagster-io/ui';
import styled from 'styled-components/macro';

interface Props {
  $top: number;
}

/**
 * Wrap a `Table` component with this to cause its `thead` to be sticky while scrolling.
 *
 * `$top` is the pixel value of the point in the scrolling container that the `thead`
 * should stick to. Probably `0`.
 */
export const StickyTableContainer = styled.div<Props>`
  thead tr {
    position: sticky;
    top: ${({$top}) => $top}px;
    background-color: ${Colors.White};
    z-index: 1;
  }

  /**
   * Safari won't render a box-shadow on the \`tr\` and we don't want an inset
   * box-shadow on \`th\` elements because it will create a double-border on the
   * bottom of the \`thead\` in the non-stuck state.
   *
   * We therefore render an absoulutely-positioned keyline on the bottom of the
   * \`th\` elements. This will appear as a border in the stuck state, and will
   * overlap the top box-shadow of the first row in the non-stuck state.
   */
  thead tr th {
    position: relative;
  }

  thead tr th::after {
    content: '';
    display: block;
    height: 1px;
    background-color: ${Colors.KeylineGray};
    position: absolute;
    bottom: -1px;
    left: 0;
    right: 0;
  }
`;
