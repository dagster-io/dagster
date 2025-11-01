import clsx from 'clsx';
import {ReactNode} from 'react';

import {Box} from './Box';
import {Icon, IconName} from './Icon';
import styles from './css/Alert.module.css';

export type AlertIntent = 'info' | 'warning' | 'error' | 'success' | 'none';

interface Props {
  intent?: AlertIntent;
  title: ReactNode;
  description?: ReactNode;
  icon?: ReactNode;
  rightButton?: ReactNode;
  onClose?: () => void;
}

type Config = {
  icon: IconName;
  className: string | undefined;
};

const configMap: Record<AlertIntent, Config> = {
  info: {
    icon: 'info',
    className: styles.info,
  },
  warning: {
    icon: 'warning',
    className: styles.warning,
  },
  error: {
    icon: 'error',
    className: styles.error,
  },
  success: {
    icon: 'success',
    className: styles.success,
  },
  none: {
    icon: 'info',
    className: styles.none,
  },
};

export const Alert = (props: Props) => {
  const {intent = 'info', title, description, rightButton, onClose} = props;
  const {className, icon} = configMap[intent];

  return (
    <Box className={clsx(styles.alert, className)} padding={{horizontal: 16, vertical: 12}}>
      <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
        <Box flex={{direction: 'row', gap: 12, alignItems: 'flex-start'}}>
          <div className={styles.icon}>{props.icon || <Icon name={icon} />}</div>
          <Box flex={{direction: 'column', gap: 8}}>
            <div className={styles.title}>{title}</div>
            {description ? <div className={styles.description}>{description}</div> : null}
          </Box>
        </Box>
        {!!onClose ? (
          <button className={styles.button} onClick={onClose}>
            <Icon name="close" />
          </button>
        ) : rightButton ? (
          <div style={{alignSelf: 'center'}}>{rightButton}</div>
        ) : null}
      </Box>
    </Box>
  );
};
