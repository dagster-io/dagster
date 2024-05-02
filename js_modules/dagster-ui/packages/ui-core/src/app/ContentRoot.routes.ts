export const ContentRootRoutes = [
  {
    path: '/asset-groups(/?.*)',
    nested: [],
  },
  {
    path: '/assets(/?.*)',
    nested: [],
  },
  {
    path: '/runs',
    nested: [],
  },
  {
    path: '/runs/scheduled',
    nested: [],
  },
  {
    path: '/runs/:runId',
    nested: [],
  },
  {
    path: '/snapshots/:pipelinePath/:tab?',
    nested: [],
  },
  {
    path: '/health',
    nested: [],
  },
  {
    path: '/concurrency',
    nested: [],
  },
  {
    path: '/config',
    nested: [],
  },
  {
    path: '/locations',
    nested: [],
  },
  {
    path: '/locations',
    nested: [],
  },
  {
    path: '/guess/:jobPath',
    nested: [],
  },
  {
    path: '/overview',
    nested: [],
  },
  {
    path: '/jobs',
    nested: [],
  },
  {
    path: '/automation',
    nested: [],
  },
  {
    path: '/settings',
    nested: [],
  },
  {
    path: '*',
    nested: [],
  },
];
