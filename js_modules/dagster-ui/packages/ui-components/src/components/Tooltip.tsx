// eslint-disable-next-line no-restricted-imports
import {Tooltip2, Tooltip2Props} from '@blueprintjs/popover2';
import deepmerge from 'deepmerge';
import * as React from 'react';
import styled, {createGlobalStyle, css} from 'styled-components';

import {Colors} from './Color';
import {FontFamily} from './styles';

export const GlobalTooltipStyle = createGlobalStyle`
  .dagster-tooltip .bp5-popover-content {
      font-family: ${FontFamily.default};
      font-size: 12px;
      line-height: 16px;
      background: ${Colors.tooltipBackground()};
      color: ${Colors.tooltipText()};
      padding: 8px 16px;
  }

  .block-tooltip.bp5-popover-target {
    display: block;
  }

  .dagster-tooltip-bare .bp5-popover-content {
    padding: 0;
  }
`;

// Overwrite arrays instead of concatting them.
const overwriteMerge = (destination: any[], source: any[]) => source;

interface Props extends Tooltip2Props {
  children: React.ReactNode;
  display?: React.CSSProperties['display'];
  canShow?: boolean;
  useDisabledButtonTooltipFix?: boolean;
}

export const Tooltip = (props: Props) => {
  const {useDisabledButtonTooltipFix = false, children, display, canShow = true, ...rest} = props;

  const [isOpen, setIsOpen] = React.useState<undefined | boolean>(undefined);

  const divRef = React.useRef<HTMLDivElement>(null);

  React.useLayoutEffect(() => {
    let listener: null | ((e: MouseEvent) => void) = null;
    if (isOpen && useDisabledButtonTooltipFix) {
      listener = (e: MouseEvent) => {
        if (!divRef.current?.contains(e.target as HTMLDivElement)) {
          setIsOpen(false);
        }
      };
      document.body.addEventListener('mousemove', listener);
    }
    return () => {
      listener && document.body.removeEventListener('mousemove', listener);
    };
  }, [isOpen, useDisabledButtonTooltipFix]);

  if (!canShow) {
    return <>{children}</>;
  }

  const styledTooltip = (
    <StyledTooltip
      isOpen={isOpen}
      {...rest}
      minimal
      $display={display}
      popoverClassName={`dagster-tooltip ${props.popoverClassName}`}
      modifiers={deepmerge(
        {offset: {enabled: true, options: {offset: [0, 8]}}},
        props.modifiers || {},
        {arrayMerge: overwriteMerge},
      )}
    >
      {children}
    </StyledTooltip>
  );

  if (useDisabledButtonTooltipFix) {
    return (
      <div
        ref={divRef}
        onMouseEnter={() => {
          setIsOpen(true);
        }}
      >
        {styledTooltip}
      </div>
    );
  }
  return styledTooltip;
};

interface StyledTooltipProps extends React.ComponentProps<typeof Tooltip2> {
  $display: React.CSSProperties['display'];
  children: React.ReactNode;
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
