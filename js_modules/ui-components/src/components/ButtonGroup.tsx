import clsx from 'clsx';
import {MouseEvent} from 'react';

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
};

interface Props<T> {
  activeItems?: Set<T>;
  buttons: ButtonGroupItem<T>[];
  onClick: (id: T, e: MouseEvent<HTMLButtonElement>) => void;
}

export const ButtonGroup = <T extends string | number>(props: Props<T>) => {
  const {activeItems, buttons, onClick} = props;
  return (
    <JoinedButtons>
      {buttons.map((button) => {
        const {id, icon, label, tooltip, disabled} = button;
        const isActive = activeItems?.has(id);
        return (
          <Tooltip content={tooltip ?? ''} canShow={!!tooltip} position="top" key={id}>
            <Button
              key={id}
              aria-selected={isActive}
              className={clsx(styles.buttonGroupItem, isActive && styles.active)}
              icon={icon ? <Icon name={icon} /> : null}
              onClick={(e) => onClick(id, e)}
              disabled={disabled}
            >
              {label}
            </Button>
          </Tooltip>
        );
      })}
    </JoinedButtons>
  );
};
