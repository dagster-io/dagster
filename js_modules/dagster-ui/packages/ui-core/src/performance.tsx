import {Fragment, useLayoutEffect, useMemo, useRef} from 'react';

import {usePageContext} from './app/analytics';

type TraceData = {
  name: string;
  startTime: number;
  endTime: number | null;
};

export type Trace = {
  startTrace: (ts?: number) => void;
  endTrace: (ts?: number) => void;
};

// @ts-expect-error - exposing a global for cypress test to access traces
window.__traceBuffer = [];
class PointToPointInstrumentation {
  private traces: {[traceId: string]: TraceData} = {};

  startTrace(traceId: string, name: string, startTime = performance.now()): void {
    if (!traceId) {
      console.error('Trace ID is required to start a trace.');
      return;
    }

    if (this.traces[traceId]) {
      return;
    }

    this.traces[traceId] = {name, startTime, endTime: null};
  }

  endTrace(traceId: string, endTime = performance.now()): void {
    if (!traceId) {
      return;
    }

    const trace = this.traces[traceId];

    if (!trace) {
      return;
    }

    if (trace.endTime) {
      return;
    }

    trace.endTime = endTime;
    // @ts-expect-error - exposing global for cypress
    window.__traceBuffer.push(trace);
    if (process.env.NODE_ENV === 'development') {
      console.log(`Finished trace ${traceId}`, trace);
    }
    if (_listeners.length) {
      _listeners.forEach((listener) => listener(trace));
    }
  }
}

const _listeners: Array<(trace: TraceData) => void> = [];
export function registerTraceListener(listener: (trace: TraceData) => void) {
  _listeners.push(listener);
  return () => {
    const idx = _listeners.indexOf(listener);
    if (idx !== -1) {
      _listeners.splice(idx, 1);
    }
  };
}

const instrumentation = new PointToPointInstrumentation();

let lastPageTransition = 0;
let counter = 0;
export function usePageLoadTrace(name: string) {
  return useMemo(() => {
    const trace = createTrace(name);
    trace.startTrace(lastPageTransition);
    return {
      endTrace: () => trace.endTrace(),
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}

export function createTrace(name: string): Trace {
  const traceId = `${counter++}:${name}`;
  return {
    startTrace: (startTime = performance.now()) =>
      instrumentation.startTrace(traceId, name, startTime),
    endTrace: (endTime = performance.now()) => instrumentation.endTrace(traceId, endTime),
  };
}

export type PageLoadTrace = ReturnType<typeof usePageLoadTrace>;

const PAGEVIEW_DELAY = 300;

export function PerformancePageNavigationListener() {
  const {path, specificPath} = usePageContext();
  const didPageViewBefore = useRef(false);

  useLayoutEffect(() => {
    // Wait briefly to allow redirects.
    const time = performance.now();
    const timer = setTimeout(() => {
      if (didPageViewBefore.current) {
        lastPageTransition = time;
      }
      didPageViewBefore.current = true;
    }, PAGEVIEW_DELAY);

    return () => {
      clearTimeout(timer);
    };
  }, [path, specificPath]);

  return <Fragment />;
}
