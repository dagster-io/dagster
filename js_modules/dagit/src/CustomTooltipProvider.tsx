import React from 'react';
import styled, {CSSProperties} from 'styled-components/macro';

export const CustomTooltipProvider: React.FunctionComponent<{}> = () => {
  const [state, setState] = React.useState<null | {
    title: string;
    style: CSSProperties;
  }>(null);

  React.useEffect(() => {
    document.addEventListener('mouseover', (ev) => {
      const el = ev.target;
      if (!(el instanceof Element)) {
        return;
      }
      if (el.getAttribute('id') === 'tooltip-container') {
        return;
      }

      const tooltipParentEl = el.closest('[data-tooltip]') as HTMLElement;
      if (!tooltipParentEl) {
        setState(null);
        return;
      }

      // There are three conditions under which the tooltip is shown. The DOM
      // element must be overflowing, truncated manually via `...` or be entirely
      // empty.
      const isOverflowing = tooltipParentEl.offsetWidth < tooltipParentEl.scrollWidth;
      const isManuallyOverflowed = tooltipParentEl.textContent?.includes('…');
      const isEmpty = !tooltipParentEl.hasChildNodes();

      if (!isOverflowing && !isManuallyOverflowed && !isEmpty) {
        setState(null);
        return;
      }

      const {tooltip, tooltipStyle} = tooltipParentEl.dataset;
      const {left, top} = tooltipParentEl.getBoundingClientRect();
      const style = {left, top};

      if (tooltipStyle) {
        const overrides = JSON.parse(tooltipStyle);
        Object.assign(style, {
          ...overrides,
          left: left + (overrides.left || 0),
          top: top + (overrides.top || 0),
        });
      }
      setState({
        title: tooltip!,
        style,
      });
    });
  }, []);

  if (!state) {
    return <span />;
  }

  return (
    <TooltipContainer id="tooltip-container" style={state.style}>
      {state.title}
    </TooltipContainer>
  );
};

const TooltipContainer = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  font-size: 11px;
  padding: 3px;
  color: #a88860;
  background: #fffaf5;
  border: 1px solid #dbc5ad;
  transform: translate(5px, 5px);
  box-shadow: 1px 1px 3px rgba(0, 0, 0, 0.2);
  z-index: 100;
  pointer-events: none;
  user-select: none;
`;
