import * as React from 'react';

import {BaseButton} from './BaseButton';
import {JoinedButtons, buildColorSet} from './Button';
import {Colors} from './Color';
import {IconName, Icon} from './Icon';
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

export const ButtonGroup = <T extends string | number>(props: Props<T>) => {
  const {activeItems, buttons, onClick} = props;
  return (
    <JoinedButtons>
      {buttons.map((button) => {
        const {id, icon, label, tooltip} = button;
        const isActive = activeItems?.has(id);
        const {fillColor, fillColorHover, iconColor, strokeColor, strokeColorHover} = buildColorSet(
          {intent: undefined, outlined: false},
        );

        const buttonElement = (
          <BaseButton
            key={id}
            fillColor={isActive ? Colors.backgroundLighterHover() : fillColor}
            fillColorHover={isActive ? Colors.backgroundLighterHover() : fillColorHover}
            textColor={isActive ? Colors.textDefault() : Colors.textLight()}
            iconColor={iconColor}
            strokeColor={isActive ? strokeColorHover : strokeColor}
            strokeColorHover={strokeColorHover}
            icon={icon ? <Icon name={icon} /> : null}
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
    </JoinedButtons>
  );
};
