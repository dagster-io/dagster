import {WEB_WORKER_FEATURE_FLAGS_KEY, getFeatureFlagsWithDefaults} from '../app/Flags';

/**
 * Wrapper for worker on the main thread.
 */
export class Worker {
  private worker: globalThis.Worker;

  private errorHandlers = Array<(error: ErrorEvent) => void>();

  constructor(url: string | URL, options?: WorkerOptions) {
    this.worker = new globalThis.Worker(url, options);
    this.worker.postMessage({
      [WEB_WORKER_FEATURE_FLAGS_KEY]: getFeatureFlagsWithDefaults(),
    });
  }

  private messageHandlerWrapper = (handler: (event: MessageEvent) => void) => {
    return (event: MessageEvent) => {
      if (event.data.type === 'error') {
        const error = new Error(event.data.error);
        error.stack = event.data.stack;
        if (this.errorHandlers.length > 0) {
          const errorEvent = new ErrorEvent('error', {error});
          this.errorHandlers.forEach((handler) => handler(errorEvent));
        } else {
          throw error;
        }
      } else {
        handler(event);
      }
    };
  };

  public onError(handler: (error: ErrorEvent) => void) {
    this.errorHandlers.push(handler);
    this.worker.addEventListener('error', handler);
    return () => {
      this.errorHandlers = this.errorHandlers.filter((h) => h !== handler);
      this.worker.removeEventListener('error', handler);
    };
  }

  public onMessage(handler: (event: MessageEvent) => void) {
    const wrappedHandler = this.messageHandlerWrapper(handler);
    this.worker.addEventListener('message', wrappedHandler);
    return () => this.worker.removeEventListener('message', wrappedHandler);
  }

  public postMessage(message: any) {
    this.worker.postMessage(message);
  }

  public terminate() {
    this.worker.terminate();
  }
}
