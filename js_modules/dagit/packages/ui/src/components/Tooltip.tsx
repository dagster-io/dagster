// eslint-disable-next-line no-restricted-imports
import {Tooltip2, Tooltip2Props} from '@blueprintjs/popover2';
import deepmerge from 'deepmerge';
import React from 'react';
import styled, {createGlobalStyle, css} from 'styled-components/macro';

import {Colors} from './Colors';
import {FontFamily} from './styles';

export const GlobalTooltipStyle = createGlobalStyle`
  .dagit-tooltip .bp3-popover2-content {
      background: ${Colors.Gray900};
      font-family: ${FontFamily.default};
      font-size: 12px;
      line-height: 16px;
      color: ${Colors.Gray50};
      padding: 8px 16px;
  }

  .block-tooltip.bp3-popover2-target {
    display: block;
  }
`;

// Overwrite arrays instead of concatting them.
const overwriteMerge = (destination: any[], source: any[]) => source;

interface Props extends Tooltip2Props {
  display?: React.CSSProperties['display'];
  canShow?: boolean;
}

export const Tooltip: React.FC<Props> = (props) => {
  const {children, display, canShow = true, ...rest} = props;

  if (!canShow) {
    return <>{children}</>;
  }

  return (
    <StyledTooltip
      {...rest}
      minimal
      $display={display}
      popoverClassName={`dagit-tooltip ${props.popoverClassName}`}
      modifiers={deepmerge(
        {offset: {enabled: true, options: {offset: [0, 8]}}},
        props.modifiers || {},
        {arrayMerge: overwriteMerge},
      )}
    >
      {children}
    </StyledTooltip>
  );
};

interface StyledTooltipProps {
  $display: React.CSSProperties['display'];
}

const StyledTooltip = styled(Tooltip2)<StyledTooltipProps>`
  ${({$display}) =>
    $display
      ? css`
          && {
            display: ${$display};
          }
        `
      : null}
`;
