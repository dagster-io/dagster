// eslint-disable-next-line no-restricted-imports
import {OverlayToaster, OverlayToasterProps} from '@blueprintjs/core';
import {createRoot} from 'react-dom/client';

// https://github.com/palantir/blueprint/issues/5212#issuecomment-1318397270
export const createToaster = (props?: OverlayToasterProps, container = document.body) => {
  const containerElement = document.createElement('div');
  container.appendChild(containerElement);
  const root = createRoot(containerElement);
  return new Promise<OverlayToaster>((resolve, reject) => {
    root.render(
      <OverlayToaster
        {...props}
        usePortal={false}
        ref={(instance) => {
          if (!instance) {
            reject(new Error('[Blueprint] Unable to create toaster.'));
          } else {
            resolve(instance);
          }
        }}
      />,
    );
  });
};
