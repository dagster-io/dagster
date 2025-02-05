import {WEB_WORKER_FEATURE_FLAGS_KEY, getFeatureFlagsWithDefaults} from '../app/Flags';

/**
 * Wrapper for worker on the main thread.
 */
export class Worker {
  private worker: globalThis.Worker;

  private errorHandlers = Array<(error: ErrorEvent) => void>();

  constructor(url: string | URL, options?: WorkerOptions) {
    this.worker = new globalThis.Worker(url, options);
    this.onMessage((event) => {
      if (event.data.type === 'error') {
        const error = new Error(event.data.error);
        error.stack = event.data.stack;
        if (this.errorHandlers.length > 0) {
          const errorEvent = new ErrorEvent('error', {error});
          this.errorHandlers.forEach((handler) => handler(errorEvent));
        } else {
          throw error;
        }
      }
    });
    this.worker.postMessage({
      [WEB_WORKER_FEATURE_FLAGS_KEY]: getFeatureFlagsWithDefaults(),
    });
  }

  onError(handler: (error: ErrorEvent) => void) {
    this.errorHandlers.push(handler);
    this.worker.addEventListener('error', handler);
    return () => {
      this.errorHandlers = this.errorHandlers.filter((h) => h !== handler);
      this.worker.removeEventListener('error', handler);
    };
  }

  onMessage(handler: (event: MessageEvent) => void) {
    this.worker.addEventListener('message', handler);
    return () => this.worker.removeEventListener('message', handler);
  }

  postMessage(message: any) {
    this.worker.postMessage(message);
  }

  terminate() {
    this.worker.terminate();
  }
}
