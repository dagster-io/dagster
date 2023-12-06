import {trace, Span} from '@opentelemetry/api';
import {WebTracerProvider} from '@opentelemetry/web';
import React from 'react';

import {usePageContext} from './app/analytics';
// Initialize OpenTelemetry
const tracerProvider = new WebTracerProvider();
trace.setGlobalTracerProvider(tracerProvider);

const tracer = trace.getTracer('custom-tracer');

// Start a span when the page starts loading to represent page-load
let pageloadSpan: Span | undefined;

export function init() {
  pageloadSpan = tracer.startSpan('page-load', {
    startTime: performance.timeOrigin,
  });
}

/**
 * This function is used by cypress to hook into the provider and add a span processor:
 *
 * // Configure Collector exporter to send traces to your Starlette backend
 * const collectorExporter = new CollectorTraceExporter({
 *   serviceName: 'web-performance',
 *   url: 'http://dagster.cloud/web-performance-trace',
 * });
 *
 * // Register exporter
 * __getProvider().addSpanProcessor(new BatchSpanProcessor(collectorExporter));
 */
export function __getProvider() {
  return tracerProvider;
}

let didPageload = false;
export function useTrace(name: string) {
  const {path} = usePageContext();
  if (!didPageload && pageloadSpan) {
    pageloadSpan.setAttribute('scenario', name);
    pageloadSpan.setAttribute('path', path);
    pageloadSpan.setAttribute('url', document.location.href);
  }

  return React.useMemo(
    () => ({
      endTrace: () => {
        if (didPageload || !pageloadSpan) {
          return;
        }
        didPageload = true;
        pageloadSpan.setAttribute('pageload_end_ms', performance.now());
        pageloadSpan.end();
        document.dispatchEvent(
          new CustomEvent('PerformanceTrace', {
            detail: pageloadSpan,
          }),
        );
      },
    }),
    [],
  );
}
