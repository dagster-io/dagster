import clsx from 'clsx';
import {ComponentPropsWithRef, ForwardedRef, ReactNode, forwardRef} from 'react';

import {Intent} from './Intent';
import {Spinner} from './Spinner';
import styles from './css/Button.module.css';

export const getButtonClassName = (intent?: Intent, outlined?: boolean) => {
  return clsx(
    styles.button,
    outlined ? styles.outlined : styles.filled,
    intent === 'danger' && styles.danger,
    intent === 'success' && styles.success,
    intent === 'warning' && styles.warning,
    intent === 'primary' && styles.primary,
    intent === 'none' && styles.none,
    intent === undefined && styles.noIntent,
  );
};

interface ButtonChildrenProps {
  left?: ReactNode;
  label?: ReactNode;
  right?: ReactNode;
}

export const ButtonChildren = ({left, label, right}: ButtonChildrenProps) => {
  return (
    <>
      {left ?? null}
      {label ? <span className={styles.buttonText}>{label}</span> : null}
      {right ?? null}
    </>
  );
};

export interface CommonButtonProps {
  icon?: ReactNode;
  label?: ReactNode;
  rightIcon?: ReactNode;
  intent?: Intent;
  outlined?: boolean;
}

interface ButtonProps extends CommonButtonProps, ComponentPropsWithRef<'button'> {
  loading?: boolean;
}

export const Button = forwardRef((props: ButtonProps, ref: ForwardedRef<HTMLButtonElement>) => {
  const {children, disabled, icon, intent, loading, outlined, rightIcon, className, ...rest} =
    props;
  const iconOrSpinner = loading ? <Spinner purpose="body-text" /> : icon;
  return (
    <button
      {...rest}
      ref={ref}
      disabled={!!(disabled || loading)}
      className={clsx(getButtonClassName(intent, outlined), className)}
    >
      <ButtonChildren left={iconOrSpinner} label={children} right={rightIcon} />
    </button>
  );
});

Button.displayName = 'Button';

export interface ExternalAnchorButtonProps extends CommonButtonProps, ComponentPropsWithRef<'a'> {}

export const ExternalAnchorButton = forwardRef(
  (props: ExternalAnchorButtonProps, ref: ForwardedRef<HTMLAnchorElement>) => {
    const {children, icon, intent, outlined, rightIcon, className, ...rest} = props;
    return (
      <a
        {...rest}
        ref={ref}
        className={clsx(getButtonClassName(intent, outlined), className)}
        target="_blank"
        rel="noreferrer nofollow"
      >
        <ButtonChildren left={icon} label={children} right={rightIcon} />
      </a>
    );
  },
);

ExternalAnchorButton.displayName = 'ExternalAnchorButton';

interface JoinedButtonsProps extends React.ComponentPropsWithRef<'div'> {}

export const JoinedButtons = ({children, className, ...rest}: JoinedButtonsProps) => {
  return (
    <div {...rest} className={clsx(styles.joinedButtons, className)}>
      {children}
    </div>
  );
};
