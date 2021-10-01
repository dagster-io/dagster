import * as React from 'react';

import {BaseButton} from './BaseButton';
import {Box} from './Box';
import {ColorsWIP} from './Colors';
import {IconName, IconWIP} from './Icon';

export type ButtonGroupItem<T> = {
  id: T;
  label?: React.ReactNode;
  icon?: IconName;
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
        const {id, icon, label} = button;
        const isActive = activeItems?.has(id);
        return (
          <BaseButton
            key={id}
            fillColor={isActive ? ColorsWIP.Gray200 : ColorsWIP.Gray50}
            textColor={isActive ? ColorsWIP.Gray900 : ColorsWIP.Gray700}
            stroke={false}
            icon={
              icon ? (
                <IconWIP name={icon} color={isActive ? ColorsWIP.Gray900 : ColorsWIP.Gray700} />
              ) : null
            }
            label={label}
            onClick={(e) => onClick(id, e)}
          />
        );
      })}
    </Box>
  );
};
