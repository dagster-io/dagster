import {Box, CustomTooltipProvider} from '@dagster-io/ui';
import {Meta} from '@storybook/react';
import React from 'react';

import {TruncatedTextWithFullTextOnHover} from '../../../nav/getLeftNavItemsForOption';
import {FilterDropdown} from '../FilterDropdown';
import {useFilters} from '../useFilters';
import {useStaticSetFilter} from '../useStaticSetFilter';
import {useTimeRangeFilter} from '../useTimeRangeFilter';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'useFilters',
  component: FilterDropdown,
} as Meta;

const TestComponent: React.FC = () => {
  const userFilter = useStaticSetFilter({
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
    getKey: (value) => value,
    renderLabel: ({value, isActive}) => (
      <span style={{color: isActive ? 'green' : undefined}}>
        <TruncatedTextWithFullTextOnHover text={value} />
      </span>
    ),
    getStringValue: (value) => value,
  });

  const testFilter = useStaticSetFilter({
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
    getKey: (value) => value,
    renderLabel: ({value, isActive}) => (
      <span style={{color: isActive ? 'green' : undefined}}>
        <TruncatedTextWithFullTextOnHover text={value} />
      </span>
    ),
    getStringValue: (value) => value,
  });

  const deploymentFilter = useStaticSetFilter({
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
  });

  const timeRangeFilter = useTimeRangeFilter({
    name: 'Timestamp',
    icon: 'date',
    timezone: 'UTC',
  });

  const filters = React.useMemo(() => [userFilter, deploymentFilter, timeRangeFilter, testFilter], [
    userFilter,
    deploymentFilter,
    timeRangeFilter,
    testFilter,
  ]);

  const {button, activeFiltersJsx} = useFilters({filters});

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
