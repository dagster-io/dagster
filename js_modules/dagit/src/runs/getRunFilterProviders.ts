export const getRunFilterProviders = (stepNames: string[] = []) => {
  return [
    {
      token: 'step',
      values: () => stepNames,
    },
    {
      token: 'type',
      values: () => ['expectation', 'materialization', 'engine', 'input', 'output', 'pipeline'],
    },
    {
      token: 'query',
      values: () => [],
    },
  ];
};
