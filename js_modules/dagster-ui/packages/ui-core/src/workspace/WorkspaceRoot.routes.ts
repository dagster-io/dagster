export const WorkspaceRootRoutes = [
  {
    path: '/locations/:repoPath/resources',
  },
  {
    path: '/locations/:repoPath/assets',
  },
  {
    path: '/locations/:repoPath/jobs',
  },
  {
    path: '/locations/:repoPath/schedules',
  },
  {
    path: '/locations/:repoPath/sensors',
  },
  {
    path: '/locations/:repoPath/graphs',
  },
  {
    path: '/locations/:repoPath/ops/:name?',
  },
  {
    path: '/locations/:repoPath/graphs/(/?.*)',
  },
  {
    path: '/locations/:repoPath/schedules/:scheduleName/:runTab?',
  },
  {
    path: '/locations/:repoPath/sensors/:sensorName',
  },
  {
    path: '/locations/:repoPath/resources/:resourceName',
  },
  {
    path: '/locations/:repoPath/*',
  },
  {
    path: '/locations/:repoPath',
  },
];
