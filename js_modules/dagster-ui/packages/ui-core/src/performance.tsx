import {useMemo} from 'react';

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
  }
}

const instrumentation = new PointToPointInstrumentation();

let counter = 0;
export function usePageLoadTrace(name: string) {
  return useMemo(() => {
    const trace = createTrace(name);
    // Set startTimestamp to 0 to indicate this trace started when the page first started loading
    // in the future this will be changed to be the timestamp of the last transition to capture
    // transition page loads
    trace.startTrace(0);
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
