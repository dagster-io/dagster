import {WEB_WORKER_FEATURE_FLAGS_KEY, setFeatureFlags} from '../app/Flags';

export const createWorkerThread = (
  onMessage: (postMessage: (message: any) => void, data: any) => Promise<void>,
  onError: (postMessage: (message: any) => void, error: Error, event: MessageEvent) => void,
) => {
  self.addEventListener('message', async (event) => {
    try {
      if (event.data[WEB_WORKER_FEATURE_FLAGS_KEY]) {
        setFeatureFlags(event.data[WEB_WORKER_FEATURE_FLAGS_KEY]);
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
