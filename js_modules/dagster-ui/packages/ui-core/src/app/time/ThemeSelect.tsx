import {Button, Icon, Menu, MenuItem, Select} from '@dagster-io/ui-components';
import {DagsterTheme} from '@dagster-io/ui-components/src/theme/theme';
import * as React from 'react';

interface Props {
  theme: DagsterTheme;
  onChange: (value: DagsterTheme) => void;
}

export const ThemeSelect = ({theme, onChange}: Props) => {
  const items = [
    {
      key: DagsterTheme.Light,
      label: 'Light',
    },
    {
      key: DagsterTheme.Dark,
      label: 'Dark',
    },
    {
      key: DagsterTheme.System,
      label: 'System setting',
    },
  ];

  const activeItem = items.find(({key}) => key === theme);

  return (
    <Select<(typeof items)[0]>
      popoverProps={{
        position: 'bottom-right',
      }}
      filterable={false}
      activeItem={activeItem}
      items={items}
      itemRenderer={(item, props) => {
        return (
          <MenuItem
            active={props.modifiers.active}
            onClick={props.handleClick}
            key={item.key}
            text={item.label}
            style={{width: '300px'}}
          />
        );
      }}
      itemListRenderer={({renderItem, filteredItems}) => {
        const renderedItems = filteredItems.map(renderItem).filter(Boolean);
        return <Menu>{renderedItems}</Menu>;
      }}
      onItemSelect={(item) => onChange(item.key)}
    >
      <Button
        rightIcon={<Icon name="arrow_drop_down" />}
        style={{minWidth: '200px', display: 'flex', justifyContent: 'space-between'}}
      >
        {activeItem?.label}
      </Button>
    </Select>
  );
};
