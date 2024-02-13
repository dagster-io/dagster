import {useStaticSetFilter} from './useStaticSetFilter';
import {InstigationStatus} from '../../graphql/types';

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
