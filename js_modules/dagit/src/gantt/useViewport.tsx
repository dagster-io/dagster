import animate from 'amator';
import * as React from 'react';

import {GanttViewport} from 'src/gantt/Constants';

/**
 * useViewport is a React hook that exposes a viewport (top/left/width/height)
 * representing the currently visible region of a scrolling contaienr <div>.
 * It uses a ResizeObserver and an onScroll handler to monitor the viewport of the
 * container. To use, spread the returned `containerProps` onto the container div.
 */
export const useViewport = (
  options: {
    initialOffset?: (el: HTMLElement) => {left: number; top: number};
  } = {},
) => {
  const ref = React.useRef<any>();
  const [offset, setOffset] = React.useState<{left: number; top: number}>({
    left: 0,
    top: 0,
  });
  const [size, setSize] = React.useState<{width: number; height: number}>({
    width: 0,
    height: 0,
  });

  const {initialOffset} = options;

  // Monitor the container for size changes (if possible, otherwise fall back)
  // to capturing the initial size only. (Only old FF).
  const measureRef = React.useCallback(() => {
    if (!ref.current) {
      return;
    }
    const onApplySize = (next: {width: number; height: number}) => {
      setSize({width: next.width, height: next.height});
      if (!ref.current.__sized && next.width !== 0 && initialOffset) {
        const targetOffset = initialOffset(ref.current);
        ref.current.scrollTop = targetOffset.top;
        ref.current.scrollLeft = targetOffset.left;
        setOffset(targetOffset);
        ref.current.__sized = true;
      }
    };

    let resizeObserver: any;
    if (ref.current instanceof HTMLElement) {
      if ('ResizeObserver' in window) {
        resizeObserver = new window['ResizeObserver']((entries: any) => {
          if (entries[0].target === ref.current) {
            onApplySize(entries[0].contentRect);
          }
        });
        resizeObserver.observe(ref.current);
      } else {
        console.warn(`No ResizeObserver support, or useViewport is attached to a non-DOM node?`);
        onApplySize(ref.current.getBoundingClientRect());
      }
    }
    return () => {
      resizeObserver?.disconnect();
    };
  }, [initialOffset]);

  React.useEffect(measureRef, [measureRef]);

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

    const onDone = () => {
      ref.current.scrollTop = targetOffset.top;
      ref.current.scrollLeft = targetOffset.left;
      setOffset(targetOffset);
      animation.current = null;
    };
    if (animated) {
      animation.current = animate(offset, targetOffset, {
        step: (v: any) => {
          ref.current.scrollTop = v.top;
          ref.current.scrollLeft = v.left;
          setOffset({left: v.left, top: v.top});
        },
        done: onDone,
      });
    } else {
      onDone();
    }
  };

  // There are scenarios where the exported `container ref` isn't attached to a component immediately
  // (eg the parent is showing a loading state). This means it may be undefined during our initial render
  // and we need to measure it when it's actually assigned a value.
  const setRef = React.useCallback(
    (el: any) => {
      if (el === ref.current) {
        return;
      }
      ref.current = el;
      measureRef();
    },
    [measureRef],
  );

  return {
    viewport: {...offset, ...size} as GanttViewport,
    containerProps: {
      ref: setRef,
      onScroll,
    },
    onMoveToViewport,
  };
};
