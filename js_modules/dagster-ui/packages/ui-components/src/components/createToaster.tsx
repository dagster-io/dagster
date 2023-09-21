// eslint-disable-next-line no-restricted-imports
import {IToasterProps, Toaster} from '@blueprintjs/core';
import * as React from 'react';

type PortalProvider = (node: React.ReactNode, container: HTMLElement, key?: string) => void;
let _portalProvider: PortalProvider;

export const registerPortalProvider = (portalProvider: PortalProvider) => {
  _portalProvider = portalProvider;
};

// https://github.com/palantir/blueprint/issues/5212#issuecomment-1318397270
export const createToaster = (props?: IToasterProps, container = document.body) => {
  const containerElement = document.createElement('div');
  container.appendChild(containerElement);

  return new Promise<Toaster>((resolve, reject) => {
    _portalProvider(
      <Toaster
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
      containerElement,
    );
  });
};
