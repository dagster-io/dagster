import {Box, CustomTooltipProvider} from '@dagster-io/ui';
import {Meta} from '@storybook/react/types-6-0';
import React from 'react';

import {TruncatedTextWithFullTextOnHover} from '../../../nav/getLeftNavItemsForOption';
import {Filter} from '../Filter';
import {FilterDropdown} from '../FilterDropdown';
import {StaticSetFilter} from '../StaticSetFilter';
import {TimeRangeFilter} from '../TimeRangeFilter';
import {useFilters} from '../useFilters';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Filters',
  component: FilterDropdown,
} as Meta;

const TestComponent: React.FC = () => {
  const filters = React.useMemo(
    () => [
      new StaticSetFilter({
        name: 'User',
        icon: 'account_circle',
        allValues: [
          value('marco'),
          value(`a super ${'long '.repeat(100)} name`),
          value(`a super ${'long '.repeat(10)} name`),
          value(`a super ${'long '.repeat(1000)} name`),
          value('polo'),
          value('hi'),
          value('test'),
          value('today'),
          value('yesterday'),
        ],
        renderLabel: ({value, isActive}) => (
          <span style={{color: isActive ? 'green' : undefined}}>
            <TruncatedTextWithFullTextOnHover text={value} />
          </span>
        ),
        getStringValue: (value) => value,
      }),
      new StaticSetFilter({
        name: 'Test set filter',
        icon: 'account_tree',
        allValues: [
          value('marco'),
          value('polo'),
          value('hi'),
          value('test'),
          value('today'),
          value('yesterday'),
        ],
        renderLabel: ({value, isActive}) => (
          <span style={{color: isActive ? 'green' : undefined}}>
            <TruncatedTextWithFullTextOnHover text={value} />
          </span>
        ),
        getStringValue: (value) => value,
      }),

      new StaticSetFilter({
        name: 'Deployment',
        icon: 'workspaces',
        allValues: [value('prod'), value('dev'), value('staging')],
        getStringValue: (value) => value,
        renderLabel: ({value}) => (
          <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
            <div
              style={{
                width: '8px',
                height: '8px',
                backgroundColor: 'black',
                borderRadius: '50%',
                margin: '4px',
              }}
            />
            <span>
              <TruncatedTextWithFullTextOnHover text={value} />
            </span>
          </Box>
        ),
      }),
      new TimeRangeFilter('Timestamp', 'account_tree', 'UTC'),
    ],
    [],
  );

  const [_activeFilters, setActiveFilters] = React.useState<Filter<any, any>[]>([]);

  const {button, activeFiltersJsx} = useFilters({filters, setActiveFilters});

  return (
    <Box flex={{gap: 8, direction: 'column'}} padding={12}>
      <div>{button}</div>
      <Box flex={{direction: 'row', gap: 6}}>{activeFiltersJsx}</Box>
    </Box>
  );
};

export const FilterDropdownStory = () => {
  return (
    <>
      <CustomTooltipProvider />
      <TestComponent />
    </>
  );
};

function value(value: string) {
  return {
    id: value,
    value,
    match: [value],
  };
}
