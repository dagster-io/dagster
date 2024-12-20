// eslint-disable-next-line no-restricted-imports
import {OverlayToasterProps, ToastProps, Toaster as ToasterInstance} from '@blueprintjs/core';
import {createGlobalStyle} from 'styled-components';

import {Colors} from './Color';
import {Icon, IconName, IconWrapper} from './Icon';
import {createToaster} from './createToaster';

export const GlobalToasterStyle = createGlobalStyle`
  .dagster-toaster {
    .bp5-toast {
      padding: 8px 12px;
      border-radius: 8px;
      font-size: 14px;
      line-height: 22px;
      color: ${Colors.alwaysWhite()};
      background-color: ${Colors.accentGray()};
    }

    .bp5-button-group {
      padding: 2px;
    }
  
    .bp5-toast-message {
      display: flex;
      align-items: center;
      padding: 6px;
      gap: 8px;
    }

    .bp5-icon-cross {
      color: ${Colors.alwaysWhite()} !important;
    }

    ${IconWrapper} {
      background-color: ${Colors.alwaysWhite()} !important;
    }

    .bp5-toast.bp5-intent-primary,
    .bp5-toast.bp5-intent-primary .bp5-button {
      background-color: ${Colors.accentGray()} !important;
    }

    .bp5-toast.bp5-intent-success,
    .bp5-toast.bp5-intent-success .bp5-button {
      background-color: ${Colors.accentBlue()} !important;
    }

    .bp5-toast.bp5-intent-warning,
    .bp5-toast.bp5-intent-warning .bp5-button {
      background-color: ${Colors.accentGray()} !important;
    }

    .bp5-toast.bp5-intent-danger,
    .bp5-toast.bp5-intent-danger .bp5-button {
      background-color: ${Colors.accentRed()} !important;
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
          <Icon name={icon} color={Colors.accentPrimary()} />
          {rest.message}
        </>
      );
    }
    return show.apply(instance, [rest, key]);
  };

  return Object.assign(instance, {show: showWithDagsterIcon}) as DToaster;
};

const asyncCreate = async (
  props?: OverlayToasterProps,
  container?: HTMLElement,
): Promise<DToaster> => {
  const instance = await createToaster({...props, className: 'dagster-toaster'}, container);
  return setup(instance);
};

export const Toaster = {
  asyncCreate,
};
