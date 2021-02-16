import memoize from 'lodash/memoize';

export const getRunFilterProviders = memoize(
  (stepNames: string[] = []) => {
    return [
      {
        token: 'step',
        values: () => stepNames,
      },
      {
        token: 'type',
        values: () => [
          'engine',
          'expectation',
          'input',
          'materialization',
          'output',
          'pipeline',
          'queue',
          'retry',
          'skipped',
          'start',
          'success',
        ],
      },
      {
        token: 'query',
        values: () => [],
      },
    ];
  },
  (stepNames: string[]) => JSON.stringify(stepNames),
);
