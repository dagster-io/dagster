import faker from 'faker';
import {useState} from 'react';

import {FilterOption, LogFilterSelect} from '../LogFilterSelect';
import {LogLevel} from '../LogLevel';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'LogFilterSelect',
  component: LogFilterSelect,
};

export const Default = () => {
  const [options, setOptions] = useState(() => {
    return Object.fromEntries(
      Object.keys(LogLevel).map((level) => {
        return [
          level,
          {
            label: level.toLowerCase(),
            count: faker.datatype.number(4000),
            enabled: false,
          },
        ];
      }),
    ) as Record<LogLevel, FilterOption>;
  });

  const onSetFilter = (level: LogLevel, enabled: boolean) => {
    setOptions((current) => {
      const filterForLevel = current[level];
      if (filterForLevel) {
        return {...current, [level]: {...filterForLevel, enabled}};
      }
      return current;
    });
  };

  return <LogFilterSelect options={options} onSetFilter={onSetFilter} />;
};
