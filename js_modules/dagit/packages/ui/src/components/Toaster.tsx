// eslint-disable-next-line no-restricted-imports
import {Toaster as BlueprintToaster, IToasterProps, IToaster, IToastProps} from '@blueprintjs/core';
import React from 'react';
import {createGlobalStyle} from 'styled-components/macro';

import {Colors} from './Colors';
import {IconName, Icon} from './Icon';

export const GlobalToasterStyle = createGlobalStyle`
  .dagster-toaster {
    .bp3-toast {
      padding: 6px;
      border-radius: 8px;
      font-size: 14px;
      line-height: 22px;
      color: ${Colors.White};
      background-color: ${Colors.Gray900};
    }

    .bp3-button-group {
      padding: 2px;
    }
  
    .bp3-toast-message {
      display: flex;
      align-items: center;
      padding: 6px;
      gap: 8px;
    }

    .bp3-toast.bp3-intent-success {
      background-color: ${Colors.Blue500};
    }

    .bp3-toast.bp3-intent-warning,
    .bp3-toast.bp3-intent-danger {
      background-color: ${Colors.Red500};
    }
  }
`;

// Patch the Blueprint Toaster to take a Dagster iconName instead of a Blueprint iconName
type DToasterShowFn = (
  props: Omit<IToastProps, 'icon'> & {icon?: IconName},
  key?: string,
) => string;
type DToaster = Omit<IToaster, 'show'> & {show: DToasterShowFn};

export const Toaster: {
  create: (props?: IToasterProps, container?: HTMLElement) => DToaster;
} = {
  create: (props, container) => {
    const instance = BlueprintToaster.create({...props, className: 'dagster-toaster'}, container);
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
  },
};
