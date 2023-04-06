import {Box, Button, Checkbox, Colors, Icon, Menu, MenuItem, Popover} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import {LogLevel} from '../graphql/types';
import {compactNumber} from '../ui/formatters';

export type FilterOption = {
  label: string;
  count: number;
  enabled: boolean;
};

interface Props {
  options: Record<LogLevel, FilterOption>;
  onSetFilter: (level: LogLevel, enabled: boolean) => void;
}

export const LogFilterSelect: React.FC<Props> = ({options, onSetFilter}) => {
  const [showMenu, setShowMenu] = React.useState(false);

  const levels = Object.keys(options);
  const values = Object.values(options);
  const enabledCount = values.reduce((accum, {enabled}) => (enabled ? accum + 1 : accum), 0);

  const onChange = (level: string) => {
    return (e: React.ChangeEvent<HTMLInputElement>) => {
      const checked = e.target.checked;
      onSetFilter(level as LogLevel, checked);
    };
  };

  return (
    <Popover
      isOpen={showMenu}
      placement="bottom-start"
      canEscapeKeyClose
      onInteraction={(nextOpenState: boolean) => setShowMenu(nextOpenState)}
      content={
        <Menu style={{width: '180px'}} aria-label="filter-options">
          {levels.map((level) => {
            const optionForLevel = options[level as keyof typeof options];
            const {label, count, enabled} = optionForLevel;
            return (
              <MenuItem
                key={level}
                tagName="div"
                shouldDismissPopover={false}
                text={
                  <Box flex={{direction: 'row', alignItems: 'center'}}>
                    <MenuCheckbox
                      id={`menu-check-${level}`}
                      checked={enabled}
                      onChange={onChange(level)}
                      label={
                        <Box
                          flex={{
                            direction: 'row',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                          }}
                          style={{flex: 1}}
                        >
                          <div>{label}</div>
                          <div style={{color: Colors.Gray500}}>{compactNumber(count)}</div>
                        </Box>
                      }
                    />
                  </Box>
                }
              />
            );
          })}
        </Menu>
      }
    >
      <FilterButton
        onClick={() => setShowMenu((current) => !current)}
        icon={<Icon name="filter_alt" />}
        rightIcon={<Icon name="expand_more" />}
      >
        Levels ({enabledCount})
      </FilterButton>
    </Popover>
  );
};

const FilterButton = styled(Button)`
  justify-content: space-between;
  width: 100%;
`;

const MenuCheckbox = styled(Checkbox)`
  display: flex;
  flex: 1;
`;
