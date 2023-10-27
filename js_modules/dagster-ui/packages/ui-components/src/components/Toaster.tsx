// eslint-disable-next-line no-restricted-imports
import {IToasterProps, ToasterInstance, ToastProps} from '@blueprintjs/core';
import React from 'react';
import {createGlobalStyle} from 'styled-components';

import {Colors} from './Colors';
import {IconName, Icon} from './Icon';
import {createToaster} from './createToaster';

export const GlobalToasterStyle = createGlobalStyle`
  .dagster-toaster {
    .bp4-toast {
      padding: 8px 12px;
      border-radius: 8px;
      font-size: 14px;
      line-height: 22px;
      color: ${Colors.White};
      background-color: ${Colors.Gray700};
    }

    .bp4-button-group {
      padding: 2px;
    }
  
    .bp4-toast-message {
      display: flex;
      align-items: center;
      padding: 6px;
      gap: 8px;
    }

    .bp4-toast.bp4-intent-primary,
    .bp4-toast.bp4-intent-primary .bp4-button {
      background-color: ${Colors.Gray700} !important;
    }

    .bp4-toast.bp4-intent-success,
    .bp4-toast.bp4-intent-success .bp4-button {
      background-color: ${Colors.Blue500} !important;
    }

    .bp4-toast.bp4-intent-warning,
    .bp4-toast.bp4-intent-warning .bp4-button {
      background-color: ${Colors.Gray700} !important;

      .bp4-icon-cross {
        color: ${Colors.Gray300} !important;
      }
    }

    .bp4-toast.bp4-intent-danger,
    .bp4-toast.bp4-intent-danger .bp4-button {
      background-color: ${Colors.Red500} !important;
    }
  }
`;

// Patch the Blueprint Toaster to take a Dagster iconName instead of a Blueprint iconName
export type DToasterShowProps = Omit<ToastProps, 'icon'> & {icon?: IconName};
export type DToasterShowFn = (props: DToasterShowProps, key?: string) => string;
export type DToaster = Omit<ToasterInstance, 'show'> & {show: DToasterShowFn};

const setup = (instance: ToasterInstance): DToaster => {
  const show = instance.show;
  const showWithDagsterIcon: DToasterShowFn = ({icon, ...rest}, key) => {
    if (icon && typeof icon === 'string') {
      rest.message = (
        <>
          <Icon name={icon} color={Colors.White} />
          {rest.message}
        </>
      );
    }
    return show.apply(instance, [rest, key]);
  };

  return Object.assign(instance, {show: showWithDagsterIcon}) as DToaster;
};

const asyncCreate = async (props?: IToasterProps, container?: HTMLElement): Promise<DToaster> => {
  const instance = await createToaster({...props, className: 'dagster-toaster'}, container);
  return setup(instance);
};

export const Toaster = {
  asyncCreate,
};
