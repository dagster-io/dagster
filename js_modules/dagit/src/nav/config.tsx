import {IconName} from '@blueprintjs/core';
import {matchPath} from 'react-router-dom';

export type NavItemConfig = {
  label: React.ReactNode;
  icon: IconName;
  to: string;
  matchingPaths: string[];
};

export const config: NavItemConfig[][] = [
  [
    {
      label: 'Runs',
      icon: 'updated',
      to: '/instance/runs',
      matchingPaths: ['/instance/runs', '/instance/runs/*', '/instance/snapshots/*'],
    },
    {
      label: 'Asset catalog',
      icon: 'th',
      to: '/instance/assets',
      matchingPaths: ['/instance/assets', '/instance/assets/*'],
    },
  ],
  [
    {
      label: 'Pipelines',
      icon: 'diagram-tree',
      to: '/workspace/pipelines',
      matchingPaths: ['/workspace/pipelines', '/workspace/:repoPath/pipelines/*'],
    },
    {
      label: 'Solids',
      icon: 'git-commit',
      to: '/workspace/solids',
      matchingPaths: ['/workspace/solids', '/workspace/:repoPath/solids/*'],
    },
    {
      label: 'Schedules',
      icon: 'time',
      to: '/workspace/schedules',
      matchingPaths: ['/workspace/schedules', '/workspace/:repoPath/schedules/*'],
    },
    {
      label: 'Sensors',
      icon: 'automatic-updates',
      to: '/workspace/sensors',
      matchingPaths: ['/workspace/sensors', '/workspace/:repoPath/sensors/*'],
    },
  ],
  [
    {
      label: 'Status',
      icon: 'dashboard',
      to: '/instance',
      matchingPaths: [
        '/instance/health',
        '/instance/schedules',
        '/instance/sensors',
        '/instance/config',
      ],
    },
    {
      label: 'Settings',
      icon: 'cog',
      to: '/settings',
      matchingPaths: ['/settings'],
    },
  ],
];

export const matchSome = (locationPath: string, matchingPaths: string[]) =>
  matchingPaths.some((path) => !!matchPath(locationPath, path));
