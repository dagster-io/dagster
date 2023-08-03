import * as React from 'react';

import {InstigationStatus} from '../../graphql/types';

import {useStaticSetFilter} from './useStaticSetFilter';

export const useInstigationStatusFilter = () => {
  return useStaticSetFilter<InstigationStatus>({
    name: 'Running state',
    icon: 'toggle_off',
    allValues: [
      {value: InstigationStatus.RUNNING, match: ['on', 'running']},
      {value: InstigationStatus.STOPPED, match: ['off', 'stopped']},
    ],
    getKey: (value) => value,
    renderLabel: ({value}) => (
      <span>{value === InstigationStatus.RUNNING ? 'Running' : 'Stopped'}</span>
    ),
    getStringValue: (value) => value,
  });
};
