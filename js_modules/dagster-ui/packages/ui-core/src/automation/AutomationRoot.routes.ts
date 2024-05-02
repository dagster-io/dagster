export const AutomationRootRoutes = [
  {
    path: '/automation/schedules',
    nested: [],
  },
  {
    path: '/automation/sensors',
    nested: [],
  },
  {
    path: '/automation/backfills/:backfillId',
    nested: [],
  },
  {
    path: '/automation/backfills',
    nested: [],
  },
  {
    path: '/automation/auto-materialize',
    nested: [],
  },
  {
    path: '*',
    nested: [],
  },
];
