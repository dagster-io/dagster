import animate from 'amator';
import * as React from 'react';

import {GanttViewport} from './Constants';

type ContainerRef = {
  element: HTMLDivElement;
  __sized: boolean;
};

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
  const ref = React.useRef<ContainerRef>();
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
      const container = ref.current;
      if (container) {
        const {element, __sized} = container;
        if (!__sized && next.width !== 0 && initialOffset) {
          const targetOffset = initialOffset(element);
          element.scrollTop = targetOffset.top;
          element.scrollLeft = targetOffset.left;
          setOffset(targetOffset);
          container.__sized = true;
        }
      }
    };

    const container = ref.current;
    const {element} = container;

    let resizeObserver: any;
    if (element instanceof HTMLElement) {
      if ('ResizeObserver' in window) {
        resizeObserver = new window['ResizeObserver']((entries: any) => {
          if (entries[0].target === element) {
            onApplySize({width: element.clientWidth, height: element.clientHeight});
          }
        });
        resizeObserver.observe(element);
      } else {
        console.warn(`No ResizeObserver support, or useViewport is attached to a non-DOM node?`);
        onApplySize({width: element.clientWidth, height: element.clientHeight});
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
    const element = ref.current?.element;

    if (!element) {
      return;
    }

    const width = element.clientWidth;
    const height = element.clientHeight;

    if (animation.current) {
      animation.current.cancel();
      animation.current = null;
    }

    targetOffset.left = Math.min(element.scrollWidth - width, Math.max(0, targetOffset.left));
    targetOffset.top = Math.min(element.scrollHeight - height, Math.max(0, targetOffset.top));

    const onDone = () => {
      element.scrollTop = targetOffset.top;
      element.scrollLeft = targetOffset.left;
      setOffset(targetOffset);
      animation.current = null;
    };
    if (animated) {
      animation.current = animate(offset, targetOffset, {
        step: (v: any) => {
          element.scrollTop = v.top;
          element.scrollLeft = v.left;
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
    (el: HTMLDivElement) => {
      if (el === ref.current?.element) {
        return;
      }

      ref.current = {
        element: el,
        __sized: false,
      };
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
