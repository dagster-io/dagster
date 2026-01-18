import clsx from 'clsx';
import * as React from 'react';

import {Colors} from './Color';
import {Icon, IconName} from './Icon';
import styles from './css/TextInput.module.css';

interface Props extends Omit<React.ComponentPropsWithRef<'input'>, 'onChange'> {
  fill?: boolean;
  icon?: IconName;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  strokeColor?: string;
  rightElement?: JSX.Element;
}

export const TextInput = React.forwardRef(
  (props: Props, ref: React.ForwardedRef<HTMLInputElement>) => {
    const {fill, icon, disabled, strokeColor, rightElement, type = 'text', ...rest} = props;

    const containerStyle = fill ? {width: '100%', flex: 1} : undefined;

    const inputStyle = strokeColor
      ? ({
          '--text-input-stroke-color': strokeColor,
          '--text-input-stroke-color-hover': strokeColor,
        } as React.CSSProperties)
      : {};

    return (
      <div className={clsx(styles.container, disabled && styles.disabled)} style={containerStyle}>
        {icon ? (
          <Icon name={icon} color={disabled ? Colors.accentGray() : Colors.accentPrimary()} />
        ) : null}
        <input
          data-lpignore="true"
          {...rest}
          className={clsx(
            styles.input,
            icon && styles.hasIcon,
            rightElement && styles.hasRightElement,
          )}
          disabled={disabled}
          ref={ref}
          type={type}
          style={inputStyle}
        />
        {rightElement ? <div className={styles.rightContainer}>{rightElement}</div> : null}
      </div>
    );
  },
);

TextInput.displayName = 'TextInput';
