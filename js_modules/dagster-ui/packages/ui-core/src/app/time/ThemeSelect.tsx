import {
  Button,
  DagsterTheme,
  Icon,
  IconName,
  Menu,
  MenuItem,
  Select,
} from '@dagster-io/ui-components';

interface Props {
  theme: DagsterTheme;
  onChange: (value: DagsterTheme) => void;
}

export const ThemeSelect = ({theme, onChange}: Props) => {
  const items = [
    {
      key: DagsterTheme.Light,
      label: 'Light',
      icon: 'sun',
    },
    {
      key: DagsterTheme.Dark,
      label: 'Dark',
      icon: 'nightlight',
    },
    {
      key: DagsterTheme.System,
      label: 'Use system setting',
      icon: 'daemon',
    },
    {
      key: DagsterTheme.LightNoRedGreen,
      label: 'Light (no red or green)',
      icon: 'sun',
    },
    {
      key: DagsterTheme.DarkNoRedGreen,
      label: 'Dark (no red or green)',
      icon: 'nightlight',
    },
    {
      key: DagsterTheme.SystemNoRedGreen,
      label: 'Use system setting (no red or green)',
      icon: 'daemon',
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
            icon={item.icon as IconName}
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
        icon={<Icon name={activeItem?.icon as IconName} />}
        rightIcon={<Icon name="arrow_drop_down" />}
        style={{minWidth: '200px', display: 'flex', justifyContent: 'space-between'}}
      >
        {activeItem?.label}
      </Button>
    </Select>
  );
};
