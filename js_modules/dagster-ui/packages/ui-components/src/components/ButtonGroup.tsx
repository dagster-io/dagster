import clsx from 'clsx';
import {MouseEvent} from 'react';

import {Box} from './Box';
import {Button, JoinedButtons} from './Button';
import {Icon, IconName} from './Icon';
import {Tooltip} from './Tooltip';
import styles from './css/Button.module.css';

export type ButtonGroupItem<T> = {
  id: T;
  label?: React.ReactNode;
  icon?: IconName;
  tooltip?: string;
  disabled?: boolean;
  testId?: string;
};

interface Props<T> {
  activeItems?: Set<T>;
  buttons: ButtonGroupItem<T>[];
  onClick: (id: T, e: MouseEvent<HTMLButtonElement>) => void;
  /** If true, buttons are joined together. If false, buttons have gaps between them. Default: true */
  joined?: boolean;
  /** Gap between buttons when joined=false. Default: 8 */
  gap?: number;
  /** Use radio semantics (aria-checked) instead of aria-selected. Useful for single selection. Default: false */
  radio?: boolean;
}

export const ButtonGroup = <T extends string | number>(props: Props<T>) => {
  const {activeItems, buttons, onClick, joined = true, gap = 8, radio = false} = props;

  const buttonElements = buttons.map((button) => {
    const {id, icon, label, tooltip, disabled, testId} = button;
    const isActive = activeItems?.has(id);

    const ariaProps = radio
      ? {role: 'radio' as const, 'aria-checked': isActive}
      : {'aria-selected': isActive};

    return (
      <Tooltip content={tooltip ?? ''} canShow={!!tooltip} position="top" key={id}>
        <Button
          key={id}
          {...ariaProps}
          className={clsx(styles.buttonGroupItem, isActive && styles.active)}
          icon={icon ? <Icon name={icon} /> : null}
          onClick={(e) => onClick(id, e)}
          disabled={disabled}
          data-testid={testId}
        >
          {label}
        </Button>
      </Tooltip>
    );
  });

  if (joined) {
    return <JoinedButtons>{buttonElements}</JoinedButtons>;
  }

  const containerProps = radio ? {role: 'radiogroup' as const} : {};

  return (
    <Box {...containerProps} flex={{direction: 'row', gap, alignItems: 'center', wrap: 'wrap'}}>
      {buttonElements}
    </Box>
  );
};
