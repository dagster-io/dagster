import {
  Popover,
  PopoverContent,
  PopoverContentProps,
  PopoverPortal,
  PopoverTrigger,
} from '@radix-ui/react-popover';
import {TooltipOptions} from 'chart.js/auto';
import {ReactElement, useLayoutEffect, useRef} from 'react';
import {Root, createRoot} from 'react-dom/client';

export type Context = Parameters<TooltipOptions<'bar' | 'line'>['external']>[0];

export const useRenderChartTooltip = (
  Component: ({context}: {context: Context}) => ReactElement,
  popoverContentProps: PopoverContentProps,
) => {
  const targetRef = useRef<HTMLDivElement | null>(null);
  const rootRef = useRef<Root | null>(null);

  useLayoutEffect(() => {
    return () => {
      if (targetRef.current) {
        targetRef.current.remove();
        rootRef.current?.unmount();
        targetRef.current = null;
        rootRef.current = null;
      }
    };
  }, []);

  return (context: Context) => {
    if (!targetRef.current) {
      const target = document.createElement('div');
      targetRef.current = target;
      rootRef.current = createRoot(target);
    }
    const {chart, tooltip} = context;

    const canvasParent = chart.canvas.parentNode;
    const target = targetRef.current;
    const root = rootRef.current;
    if (!canvasParent || !target || !root) {
      return;
    }

    const dataPoints = tooltip.dataPoints;
    // It's possible to interact with the chart before any data appears, and the
    // tooltip plugin just plows right ahead with trying to render. Bail in this case
    // to avoid runtime errors.
    if (!dataPoints || !dataPoints[0]) {
      return;
    }

    if (!canvasParent.contains(target)) {
      canvasParent.appendChild(target);
    }

    const {offsetLeft: positionX, offsetTop: positionY} = chart.canvas;
    target.style.position = 'absolute';
    target.style.left = positionX + tooltip.caretX + 'px';
    target.style.top = positionY + tooltip.caretY + 'px';
    target.style.zIndex = '1';

    root.render(
      <PopoverWrapper context={context} popoverContentProps={popoverContentProps}>
        <Component context={context} />
      </PopoverWrapper>,
    );
  };
};

const PopoverWrapper = ({
  children,
  popoverContentProps,
  context,
}: {
  children: ReactElement;
  popoverContentProps: PopoverContentProps;
  context: Context;
}) => {
  const {tooltip} = context;
  return (
    <Popover open={tooltip.active}>
      <PopoverTrigger style={{visibility: 'hidden'}} />
      <PopoverPortal forceMount>
        <PopoverContent
          forceMount
          style={{
            zIndex: 1,
            outline: 'none',
            opacity: tooltip.opacity,
            display: tooltip.opacity === 0 ? 'none' : 'initial',
          }}
          {...popoverContentProps}
        >
          {children}
        </PopoverContent>
      </PopoverPortal>
    </Popover>
  );
};
