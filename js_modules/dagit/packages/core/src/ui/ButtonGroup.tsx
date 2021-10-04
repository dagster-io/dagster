import * as React from 'react';

import {BaseButton} from './BaseButton';
import {Box} from './Box';
import {ColorsWIP} from './Colors';
import {IconName, IconWIP} from './Icon';
import {Tooltip} from './Tooltip';

export type ButtonGroupItem<T> = {
  id: T;
  label?: React.ReactNode;
  icon?: IconName;
  tooltip?: string;
};

interface Props<T> {
  activeItems?: Set<T>;
  buttons: ButtonGroupItem<T>[];
  onClick: (id: T, e: React.MouseEvent<HTMLButtonElement>) => void;
}

export const ButtonGroup = <T extends string>(props: Props<T>) => {
  const {activeItems, buttons, onClick} = props;
  return (
    <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
      {buttons.map((button) => {
        const {id, icon, label, tooltip} = button;
        const isActive = activeItems?.has(id);
        const buttonElement = (
          <BaseButton
            key={id}
            fillColor={isActive ? ColorsWIP.Gray200 : ColorsWIP.Gray50}
            textColor={isActive ? ColorsWIP.Gray900 : ColorsWIP.Gray700}
            strokeColor="transparent"
            icon={
              icon ? (
                <IconWIP name={icon} color={isActive ? ColorsWIP.Gray900 : ColorsWIP.Gray700} />
              ) : null
            }
            label={label}
            onClick={(e) => onClick(id, e)}
          />
        );

        if (tooltip) {
          return (
            <Tooltip content={tooltip} position="top" key={id}>
              {buttonElement}
            </Tooltip>
          );
        }

        return buttonElement;
      })}
    </Box>
  );
};
