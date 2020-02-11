import * as React from "react";
import { GaantViewport } from "./Constants";

/**
 * useViewport is a React hook that exposes a viewport (top/left/width/height)
 * representing the currently visible region of a scrolling contaienr <div>.
 * It uses a ResizeObserver and an onScroll handler to monitor the viewport of the
 * container. To use, spread the returned `containerProps` onto the container div.
 */
export const useViewport = () => {
  const ref = React.useRef<any>();
  const [offset, setOffset] = React.useState<{ left: number; top: number }>({
    left: 0,
    top: 0
  });
  const [size, setSize] = React.useState<{ width: number; height: number }>({
    width: 0,
    height: 0
  });

  // Monitor the container for size changes (if possible, otherwise fall back)
  // to capturing the initial size only. (Only old FF).
  React.useEffect(() => {
    if (!ref.current) {
      return;
    }
    let resizeObserver: any;
    if (ref.current instanceof HTMLElement && "ResizeObserver" in window) {
      resizeObserver = new window["ResizeObserver"]((entries: any) => {
        setSize({
          width: entries[0].contentRect.width,
          height: entries[0].contentRect.height
        });
      });
      resizeObserver.observe(ref.current);
    } else {
      const rect = ref.current.getBoundingClientRect();
      setSize({ width: rect.width, height: rect.height });
    }
    return () => {
      resizeObserver?.disconnect();
    };
  }, []);

  // Monitor the container for scroll offset changes
  const onScroll = (e: React.UIEvent) => {
    setOffset({
      left: e.currentTarget.scrollLeft,
      top: e.currentTarget.scrollTop
    });
  };

  return {
    viewport: { ...offset, ...size } as GaantViewport,
    containerProps: { ref, onScroll }
  };
};
