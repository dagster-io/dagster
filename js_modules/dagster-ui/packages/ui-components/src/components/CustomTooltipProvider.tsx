import {useEffect, useState} from 'react';
import styled from 'styled-components';

import {Colors} from './Color';

export const CustomTooltipProvider = () => {
  const [state, setState] = useState<null | {
    title: string;
    style: React.CSSProperties;
  }>(null);

  useEffect(() => {
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
      if (!tooltip) {
        setState(null);
        return;
      }

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
        title: tooltip,
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
  font-size: 12px;
  padding: 4px 6px;
  color: ${Colors.tooltipText()};
  background: ${Colors.tooltipBackground()};
  transform: translate(5px, 5px);
  box-shadow: 1px 1px 3px ${Colors.shadowDefault()}};
  z-index: 100;
  pointer-events: none;
  user-select: none;
`;
