import type {Message} from './runLogs';

type SHUTDOWN = {
  type: 'SHUTDOWN';
  staticPathRoot?: undefined;
};

self.addEventListener('message', ({data}: {data: Message | SHUTDOWN}) => {
  if (data.staticPathRoot) {
    __webpack_public_path__ = data.staticPathRoot;
  }
  Promise.all([import('../util'), import('./apolloClient'), import('./runLogs')]).then(
    ([{stringToArrayBuffers}, {setup, getApolloClient, stop}, {onMainThreadMessage}]) => {
      switch (data.type) {
        case 'SHUTDOWN':
          stop();
          break;
        case 'INITIALIZE':
          setup(data);
          onMainThreadMessage({
            ...data,
            getApolloClient,
            postMessage: (data: any) => {
              // Transfer data using ArrayBuffer to keep main thread buttery smooth
              const buffers = stringToArrayBuffers(JSON.stringify(data));
              // "When an ArrayBuffer is transferred between threads, the
              // memory resource that it points to is literally moved between
              // contexts in a fast and efficient zero-copy operation."
              self.postMessage('startChunk');
              buffers.forEach((buffer) => {
                // eslint-disable-next-line @typescript-eslint/ban-ts-comment
                // @ts-ignore https://developer.mozilla.org/en-US/docs/Glossary/Transferable_objects
                self.postMessage(buffer, [buffer]);
              });
              self.postMessage('endChunk');
            },
          });
          break;
      }
    },
  );
});
