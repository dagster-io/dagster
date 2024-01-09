import React from 'react';

type TraceData = {
  name: string;
  startTime: number;
  endTime: number | null;
};

// @ts-expect-error - exposing a global for cypress test to access traces
window.__traceBuffer = [];
class PointToPointInstrumentation {
  private traces: {[traceId: string]: TraceData} = {};

  startTrace(traceId: string, name: string): void {
    if (!traceId) {
      console.error('Trace ID is required to start a trace.');
      return;
    }

    if (this.traces[traceId]) {
      return;
    }

    const startTime = performance.now();
    this.traces[traceId] = {name, startTime, endTime: null};
  }

  endTrace(traceId: string): void {
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

    trace.endTime = performance.now();
    // @ts-expect-error - exposing global for cypress
    window.__traceBuffer.push(trace);
    if (process.env.NODE_ENV === 'development') {
      console.log(`Finished trace ${traceId}`);
    }
  }
}

const instrumentation = new PointToPointInstrumentation();

let counter = 0;
export function useStartTrace(name: string) {
  const traceId = React.useMemo(() => `${counter++}:${name}`, [name]);

  instrumentation.startTrace(traceId, name);

  return React.useMemo(
    () => ({
      endTrace: instrumentation.endTrace.bind(instrumentation, traceId),
    }),
    [traceId],
  );
}

export type Trace = ReturnType<typeof useStartTrace>;
