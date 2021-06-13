import memoize from 'lodash/memoize';

import {DagsterEventType} from '../types/globalTypes';

const typeValues = memoize(() => Object.values(DagsterEventType).sort());

export const getRunFilterProviders = memoize(
  (stepNames: string[] = []) => {
    return [
      {
        token: 'step',
        values: () => stepNames,
      },
      {
        token: 'type',
        values: typeValues,
      },
      {
        token: 'query',
        values: () => [],
      },
    ];
  },
  (stepNames: string[] = []) => JSON.stringify(stepNames),
);
