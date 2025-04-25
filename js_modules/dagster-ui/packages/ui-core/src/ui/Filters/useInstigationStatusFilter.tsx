import {InstigationStatus} from '../../graphql/types';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {useStaticSetFilter} from '../BaseFilters/useStaticSetFilter';

export const useInstigationStatusFilter = () => {
  const [state, onStateChanged] = useQueryPersistedState<Set<InstigationStatus>>({
    encode: (vals) => ({instigationStatus: vals.size ? Array.from(vals).join(',') : undefined}),
    decode: (qs) => {
      const status = qs.instigationStatus;
      if (typeof status === 'string') {
        return new Set(status.split(',') as InstigationStatus[]);
      }
      return new Set();
    },
  });
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
    state,
    onStateChanged,
    getStringValue: (value) => value,
  });
};
