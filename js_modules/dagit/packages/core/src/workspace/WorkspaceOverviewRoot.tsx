import * as React from 'react';

import {useTrackPageView} from '../app/analytics';

import {WorkspaceOverviewWithGrid} from './WorkspaceOverviewWithGrid';

export const WorkspaceOverviewRoot = () => {
  useTrackPageView();

  return <WorkspaceOverviewWithGrid />;
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default WorkspaceOverviewRoot;
