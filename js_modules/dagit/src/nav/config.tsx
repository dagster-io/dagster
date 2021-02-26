import {IconName} from '@blueprintjs/core';
import * as React from 'react';
import {matchPath} from 'react-router-dom';

import {InstanceWarningIcon} from 'src/nav/InstanceWarningIcon';
import {Group} from 'src/ui/Group';

export type KeyShortcut = {
  code: string;
  modifier?: string;
};

export type NavItemConfig = {
  label: React.ReactNode;
  icon: IconName;
  to: string;
  matchingPaths: string[];
  shortcut?: KeyShortcut;
};

export const config: NavItemConfig[][] = [
  [
    {
      label: 'Runs',
      icon: 'updated',
      to: '/instance/runs',
      matchingPaths: ['/instance/runs', '/instance/runs/*', '/instance/snapshots/*'],
      shortcut: {code: 'KeyR'},
    },
    {
      label: 'Asset catalog',
      icon: 'th',
      to: '/instance/assets',
      matchingPaths: ['/instance/assets', '/instance/assets/*'],
      shortcut: {code: 'KeyA'},
    },
  ],
  [
    {
      label: 'Pipelines',
      icon: 'diagram-tree',
      to: '/workspace/pipelines',
      matchingPaths: ['/workspace/pipelines', '/workspace/:repoPath/pipelines/*'],
      shortcut: {code: 'KeyP'},
    },
    {
      label: 'Solids',
      icon: 'git-commit',
      to: '/workspace/solids',
      matchingPaths: ['/workspace/solids', '/workspace/:repoPath/solids/*'],
      shortcut: {code: 'KeyS'},
    },
    {
      label: 'Schedules',
      icon: 'time',
      to: '/schedules',
      matchingPaths: ['/schedules', '/workspace/:repoPath/schedules/*'],
      shortcut: {code: 'KeyC'},
    },
    {
      label: 'Sensors',
      icon: 'automatic-updates',
      to: '/sensors',
      matchingPaths: ['/sensors', '/workspace/:repoPath/sensors/*'],
      shortcut: {code: 'KeyN'},
    },
  ],
  [
    {
      label: (
        <Group direction="row" spacing={8} alignItems="center">
          <div>Instance</div>
          <InstanceWarningIcon />
        </Group>
      ),
      icon: 'dashboard',
      to: '/instance',
      matchingPaths: [
        '/instance/health',
        '/instance/schedules',
        '/instance/sensors',
        '/instance/config',
      ],
      shortcut: {code: 'KeyI'},
    },
    {
      label: 'Settings',
      icon: 'cog',
      to: '/settings',
      matchingPaths: ['/settings'],
      shortcut: {code: 'KeyT'},
    },
  ],
];

export const matchSome = (locationPath: string, matchingPaths: string[]) =>
  matchingPaths.some((path) => !!matchPath(locationPath, path));
