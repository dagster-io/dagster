import {Button, Icon, IconName, MenuItem, Select} from '@dagster-io/ui-components';

import {GroupRunsBy} from './useGroupTimelineRunsBy';
import {assertUnreachable} from '../app/Util';

interface Props {
  value: GroupRunsBy;
  onSelect: (value: GroupRunsBy) => void;
}

export const GroupTimelineRunsBySelect = ({value, onSelect}: Props) => {
  return (
    <Select<GroupRunsBy>
      items={['automation', 'job']}
      itemRenderer={(item, props) => (
        <MenuItem
          key={item}
          icon={valueToIcon(item)}
          text={valueToLabel(item)}
          onClick={props.handleClick}
        />
      )}
      onItemSelect={onSelect}
      filterable={false}
    >
      <Button icon={<Icon name={valueToIcon(value)} />} rightIcon={<Icon name="arrow_drop_down" />}>
        {valueToLabel(value)}
      </Button>
    </Select>
  );
};

const valueToLabel = (value: GroupRunsBy) => {
  switch (value) {
    case 'automation':
      return 'Automation';
    case 'job':
      return 'Job';
    default:
      return assertUnreachable(value);
  }
};

const valueToIcon = (value: GroupRunsBy): IconName => {
  switch (value) {
    case 'automation':
      return 'sensors';
    case 'job':
      return 'job';
    default:
      return assertUnreachable(value);
  }
};
