import {WEB_WORKER_FEATURE_FLAGS_KEY, setFeatureFlags} from '../../app/Flags';

export const createWorkerThread = (
  onMessage: (postMessage: (message: any) => void, data: any) => Promise<void>,
  onError: (postMessage: (message: any) => void, error: Error, event: MessageEvent) => void,
) => {
  self.addEventListener('message', async (event: MessageEvent) => {
    try {
      if (event.data[WEB_WORKER_FEATURE_FLAGS_KEY]) {
        // Don't broadcast the feature flags update to the main thread.
        // or we will end up in an infinite loop.
        setFeatureFlags(event.data[WEB_WORKER_FEATURE_FLAGS_KEY], false);
      } else {
        await onMessage(self.postMessage, event.data);
      }
    } catch (error) {
      if (error instanceof Error) {
        self.postMessage({type: 'error', error: error.message, stack: error.stack});
      } else {
        self.postMessage({type: 'error', error: String(error), stack: undefined});
      }
      onError(self.postMessage, error as Error, event);
    }
  });
};
