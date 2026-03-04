import {useEffect, useState} from 'react';

import styles from './css/CustomTooltipProvider.module.css';

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
    <div id="tooltip-container" className={styles.tooltipContainer} style={state.style}>
      {state.title}
    </div>
  );
};
