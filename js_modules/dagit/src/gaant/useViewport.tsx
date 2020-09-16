import animate from 'amator';
import * as React from 'react';

import {GaantViewport} from './Constants';

/**
 * useViewport is a React hook that exposes a viewport (top/left/width/height)
 * representing the currently visible region of a scrolling contaienr <div>.
 * It uses a ResizeObserver and an onScroll handler to monitor the viewport of the
 * container. To use, spread the returned `containerProps` onto the container div.
 */
export const useViewport = () => {
  const ref = React.useRef<any>();
  const [offset, setOffset] = React.useState<{left: number; top: number}>({
    left: 0,
    top: 0,
  });
  const [size, setSize] = React.useState<{width: number; height: number}>({
    width: 0,
    height: 0,
  });

  // Monitor the container for size changes (if possible, otherwise fall back)
  // to capturing the initial size only. (Only old FF).
  const measureRef = () => {
    if (!ref.current) {
      return;
    }
    let resizeObserver: any;
    if (ref.current instanceof HTMLElement && 'ResizeObserver' in window) {
      resizeObserver = new window['ResizeObserver']((entries: any) => {
        setSize({
          width: entries[0].contentRect.width,
          height: entries[0].contentRect.height,
        });
      });
      resizeObserver.observe(ref.current);
    } else {
      console.warn(`No ResizeObsrever support, or useViewport is attached to a non-DOM node?`);
      const rect = ref.current.getBoundingClientRect();
      setSize({width: rect.width, height: rect.height});
    }
    return () => {
      resizeObserver?.disconnect();
    };
  };
  React.useEffect(measureRef, []);

  // Monitor the container for scroll offset changes
  const animation = React.useRef<any>(null);

  const onScroll = (e: React.UIEvent) => {
    if (
      Math.floor(offset.left) === e.currentTarget.scrollLeft &&
      Math.floor(offset.top) === e.currentTarget.scrollTop
    ) {
      return;
    }
    if (animation.current) {
      animation.current.cancel();
    }
    setOffset({
      left: e.currentTarget.scrollLeft,
      top: e.currentTarget.scrollTop,
    });
  };

  const onMoveToViewport = (targetOffset: {left: number; top: number}, animated: boolean) => {
    if (animation.current) {
      animation.current.cancel();
      animation.current = null;
    }

    targetOffset.left = Math.min(
      ref.current.scrollWidth - size.width,
      Math.max(0, targetOffset.left),
    );
    targetOffset.top = Math.min(
      ref.current.scrollHeight - size.height,
      Math.max(0, targetOffset.top),
    );

    if (!animated) {
      setOffset(targetOffset);
    }
    animation.current = animate(offset, targetOffset, {
      step: (v: any) => {
        ref.current.scrollTop = v.top;
        ref.current.scrollLeft = v.left;
        setOffset({
          left: v.left,
          top: v.top,
        });
      },
      done: () => {
        ref.current.scrollTop = targetOffset.top;
        ref.current.scrollLeft = targetOffset.left;
        setOffset(targetOffset);
        animation.current = null;
      },
    });
  };

  // There are scenarios where the exported `container ref` isn't attached to a component immediately
  // (eg the parent is showing a loading state). This means it may be undefined during our initial render
  // and we need to measure it when it's actually assigned a value.
  const setRef = React.useCallback((el: any) => {
    if (el === ref.current) return;
    ref.current = el;
    measureRef();
  }, []);

  return {
    viewport: {...offset, ...size} as GaantViewport,
    containerProps: {
      ref: setRef,
      onScroll,
    },
    onMoveToViewport,
  };
};
