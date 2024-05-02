export const ContentRootRoutes = [
  {
    path: '/asset-groups(/?.*)',
  },
  {
    path: '/assets(/?.*)',
  },
  {
    path: '/runs',
  },
  {
    path: '/runs/scheduled',
  },
  {
    path: '/runs/:runId',
  },
  {
    path: '/snapshots/:pipelinePath/:tab?',
  },
  {
    path: '/health',
  },
  {
    path: '/concurrency',
  },
  {
    path: '/config',
  },
  {
    path: '/locations',
  },
  {
    path: '/locations',
  },
  {
    path: '/guess/:jobPath',
  },
  {
    path: '/overview',
  },
  {
    path: '/jobs',
  },
  {
    path: '/automation',
  },
  {
    path: '/settings',
  },
  {
    path: '*',
  },
];
