import {MouseEvent, ReactNode} from 'react';
import {ExternalToast, toast} from 'sonner';

import {Box} from './Box';
import {Button} from './Button';
import {Colors} from './Color';
import {Icon, IconName} from './Icon';
import styles from './css/Toaster.module.css';

export {Toaster, toast} from 'sonner';

type Intent = 'success' | 'warning' | 'danger' | 'primary' | 'none';

export type ToastConfig = {
  intent: Intent;
  message: ReactNode;
  icon?: IconName;
  timeout?: number;
  action?:
    | {
        type: 'button';
        text: string;
        onClick: (e: MouseEvent<HTMLButtonElement>) => void;
      }
    | {type: 'custom'; element: ReactNode};
};

export const showToast = async (config: ToastConfig, sonnerConfig: ExternalToast = {}) => {
  const {intent, message, icon, timeout, action} = config;
  return toast.custom(
    (id) => {
      return (
        <Toast
          id={id}
          intent={intent}
          message={message}
          icon={icon}
          timeout={timeout}
          action={action}
        />
      );
    },
    {duration: timeout, ...sonnerConfig},
  );
};

interface ToastProps extends ToastConfig {
  id: string | number;
}

const Toast = (props: ToastProps) => {
  const {id, intent, message, icon, action} = props;
  const {backgroundColor, icon: iconFromIntent} = intentToStyles[intent];
  const iconName = icon ?? iconFromIntent;

  const actionElement = () => {
    if (!action) {
      return null;
    }

    if (action.type === 'custom') {
      return action.element;
    }

    return (
      <Button
        outlined
        className={styles.toastButton}
        onClick={(e) => {
          if (action.onClick) {
            action.onClick(e);
          }
          toast.dismiss(id);
        }}
      >
        {action.text}
      </Button>
    );
  };

  return (
    <div className={styles.toastContainer}>
      <Box
        padding={16}
        background={backgroundColor}
        border={{side: 'all', width: 1, color: backgroundColor}}
        flex={{direction: 'row', alignItems: 'center', gap: 8}}
        className={styles.toastInner}
      >
        <Box flex={{direction: 'row', alignItems: 'flex-start', gap: 8}}>
          {iconName ? <Icon name={iconName} color={Colors.accentPrimary()} /> : null}
          <div className={styles.toastMessage}>{message}</div>
        </Box>
        {actionElement()}
      </Box>
    </div>
  );
};

type ToastStyleForIntent = {
  backgroundColor: string;
  icon: IconName;
};

const intentToStyles: Record<Intent, ToastStyleForIntent> = {
  success: {
    backgroundColor: Colors.backgroundBlue(),
    icon: 'success',
  },
  warning: {
    backgroundColor: Colors.backgroundYellow(),
    icon: 'warning',
  },
  danger: {
    backgroundColor: Colors.backgroundRed(),
    icon: 'error',
  },
  primary: {
    backgroundColor: Colors.backgroundBlue(),
    icon: 'info',
  },
  none: {
    backgroundColor: Colors.backgroundGray(),
    icon: 'info',
  },
};
