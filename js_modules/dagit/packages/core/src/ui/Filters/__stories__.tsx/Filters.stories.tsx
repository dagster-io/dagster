import {Box} from '@dagster-io/ui';
import {Meta} from '@storybook/react/types-6-0';
import React from 'react';

import {Filter} from '../Filter';
import {FilterDropdown} from '../FilterDropdown';
import {SetFilter} from '../SetFilter';
import {TimeRangeFilter} from '../TimeRangeFilter';
import {useFilters} from '../useFilters';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'FilterDropdown',
  component: FilterDropdown,
} as Meta;

const TestComponent: React.FC = () => {
  const filters = React.useMemo(
    () => [
      new SetFilter({
        name: 'User',
        icon: 'account_circle',
        allValues: [value('marco'), value('polo'), value('hi')],
        renderLabel: (value) => <div>{value}</div>,
        getStringValue: (value) => value,
      }),
      new TimeRangeFilter('Timestamp', 'account_tree'),
    ],
    [],
  );

  const [activeFilters, setActiveFilters] = React.useState<Filter<any, any>[]>([]);

  const {button, activeFiltersJsx} = useFilters({filters, activeFilters, setActiveFilters});

  return (
    <Box flex={{gap: 8, direction: 'column'}} padding={12}>
      <div>{button}</div>
      <Box flex={{direction: 'row', gap: 6}}>{activeFiltersJsx}</Box>
    </Box>
  );
};

export const FilterDropdownStory = () => {
  return <TestComponent />;
};

function value(value: string) {
  return {
    id: value,
    value,
    match: [value],
  };
}
