import {Icon, Menu, MenuItem, Select, Button} from '@dagster-io/ui-components';
import {DagsterTheme} from '@dagster-io/ui-components/src/theme/theme';
import * as React from 'react';

interface Props {
  theme: DagsterTheme;
  onChange: (value: DagsterTheme) => void;
}

export const ThemeSelect = ({theme, onChange}: Props) => {
  const items = [
    {
      key: DagsterTheme.Legacy,
      label: 'Legacy',
    },
    {
      key: DagsterTheme.Light,
      label: 'Light (experimental)',
    },
    {
      key: DagsterTheme.Dark,
      label: 'Dark (experimental)',
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
        position: 'bottom-left',
        modifiers: {offset: {enabled: true, offset: '-12px, 8px'}},
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
      <Button rightIcon={<Icon name="arrow_drop_down"/>}>
        {activeItem?.label}
      </Button>
    </Select>
  );
};
