import * as React from 'react';

import {useTrackPageView} from '../app/analytics';

import {WorkspaceOverviewWithGrid} from './WorkspaceOverviewWithGrid';

export const WorkspaceOverviewRoot = () => {
  useTrackPageView();

  return <WorkspaceOverviewWithGrid />;
};
