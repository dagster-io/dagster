export const WorkspaceRootRoutes = [
  {
    path: '/locations/:repoPath/resources',
    nested: [],
  },
  {
    path: '/locations/:repoPath/assets',
    nested: [],
  },
  {
    path: '/locations/:repoPath/jobs',
    nested: [],
  },
  {
    path: '/locations/:repoPath/schedules',
    nested: [],
  },
  {
    path: '/locations/:repoPath/sensors',
    nested: [],
  },
  {
    path: '/locations/:repoPath/graphs',
    nested: [],
  },
  {
    path: '/locations/:repoPath/ops/:name?',
    nested: [],
  },
  {
    path: '/locations/:repoPath/graphs/(/?.*)',
    nested: [],
  },
  {
    path: '/locations/:repoPath/schedules/:scheduleName/:runTab?',
    nested: [],
  },
  {
    path: '/locations/:repoPath/sensors/:sensorName',
    nested: [],
  },
  {
    path: '/locations/:repoPath/resources/:resourceName',
    nested: [],
  },
  {
    path: '/locations/:repoPath/*',
    nested: [],
  },
  {
    path: '/locations/:repoPath',
    nested: [],
  },
];
