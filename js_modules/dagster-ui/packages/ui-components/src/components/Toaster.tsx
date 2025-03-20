import {MouseEvent, ReactNode} from 'react';
import {ExternalToast, toast} from 'sonner';

import {BaseButton} from './BaseButton';
import {Box} from './Box';
import {Colors} from './Color';
import {Icon, IconName} from './Icon';
import {FontFamily} from './styles';

export {Toaster} from 'sonner';

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
  const {intent, message, timeout, action} = config;
  return toast.custom(
    (id) => {
      return <Toast id={id} intent={intent} message={message} timeout={timeout} action={action} />;
    },
    {duration: timeout, ...sonnerConfig},
  );
};

interface ToastProps extends ToastConfig {
  id: string | number;
}

const Toast = (props: ToastProps) => {
  const {id, intent, message, action} = props;
  const {backgroundColor, textColor, icon, iconColor} = intentToStyles(intent);

  const actionElement = () => {
    if (!action) {
      return null;
    }

    if (action.type === 'custom') {
      return action.element;
    }

    return (
      <BaseButton
        fillColor={Colors.backgroundGray()}
        fillColorHover={Colors.backgroundGrayHover()}
        textColor={Colors.textDefault()}
        strokeColor={Colors.backgroundGray()}
        strokeColorHover={Colors.backgroundGrayHover()}
        label={action.text}
        style={{fontSize: 13, fontFamily: FontFamily.default}}
        onClick={(e) => {
          if (action.onClick) {
            action.onClick(e);
          }
          toast.dismiss(id);
        }}
      />
    );
  };

  return (
    <div style={{backgroundColor: Colors.backgroundDefault(), borderRadius: 8}}>
      <Box
        padding={16}
        background={backgroundColor}
        border={{side: 'all', width: 1, color: backgroundColor}}
        flex={{direction: 'row', alignItems: 'center', gap: 8}}
        style={{borderRadius: 8, fontSize: 13, fontFamily: FontFamily.default}}
      >
        {icon ? <Icon name={icon} color={iconColor} /> : null}
        <div style={{color: textColor}}>{message}</div>
        {actionElement()}
      </Box>
    </div>
  );
};

type ToastStyleForIntent = {
  backgroundColor: string;
  textColor: string;
  icon: IconName;
  iconColor: string;
};

const intentToStyles = (intent: Intent): ToastStyleForIntent => {
  switch (intent) {
    case 'success':
      return {
        backgroundColor: Colors.backgroundBlue(),
        textColor: Colors.textBlue(),
        icon: 'success',
        iconColor: Colors.accentBlue(),
      };
    case 'warning':
      return {
        backgroundColor: Colors.backgroundYellow(),
        textColor: Colors.textYellow(),
        icon: 'warning',
        iconColor: Colors.accentYellow(),
      };
    case 'danger':
      return {
        backgroundColor: Colors.backgroundRed(),
        textColor: Colors.textRed(),
        icon: 'error',
        iconColor: Colors.accentRed(),
      };
    case 'primary':
      return {
        backgroundColor: Colors.backgroundBlue(),
        textColor: Colors.textBlue(),
        icon: 'info',
        iconColor: Colors.accentBlue(),
      };
    case 'none':
    default:
      return {
        backgroundColor: Colors.backgroundGray(),
        textColor: Colors.textDefault(),
        icon: 'info',
        iconColor: Colors.accentPrimary(),
      };
  }
};
