import * as RadixRadioGroup from '@radix-ui/react-radio-group';
import clsx from 'clsx';
import * as React from 'react';

import styles from './css/Radio.module.css';

type RadioGroupProps = Omit<
  React.ComponentPropsWithoutRef<typeof RadixRadioGroup.Root>,
  'className'
> & {
  className?: string;
};

export const RadioGroup = ({className, ...props}: RadioGroupProps) => (
  <RadixRadioGroup.Root className={clsx(styles.radioGroup, className)} {...props} />
);

interface RadioProps {
  value: string;
  disabled?: boolean;
  className?: string;
  children?: React.ReactNode;
  'data-testid'?: string | null;
}

export const Radio = ({
  value,
  disabled,
  className,
  children,
  'data-testid': dataTestId,
}: RadioProps) => (
  <label className={clsx(styles.radio, className)} data-disabled={disabled ? '' : undefined}>
    <RadixRadioGroup.Item
      value={value}
      disabled={disabled}
      className={styles.indicator}
      data-testid={dataTestId ?? undefined}
    >
      <RadixRadioGroup.Indicator className={styles.indicatorDot} />
    </RadixRadioGroup.Item>
    {children}
  </label>
);

export const RadioContainer = ({
  children,
  className,
  ...rest
}: React.ComponentPropsWithRef<'div'>) => (
  <div {...rest} className={clsx(styles.radioContainer, className)}>
    {children}
  </div>
);
