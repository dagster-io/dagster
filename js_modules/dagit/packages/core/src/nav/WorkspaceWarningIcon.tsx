import {Colors, Icon} from '@blueprintjs/core';
import * as React from 'react';

import {WorkspaceContext} from '../workspace/WorkspaceContext';

import {WarningTooltip} from './WarningTooltip';

export const WorkspaceWarningIcon = React.memo(() => {
  const {locationEntries} = React.useContext(WorkspaceContext);

  const repoErrors = locationEntries.filter(
    (locationEntry) => locationEntry.locationOrLoadError?.__typename === 'PythonError',
  );

  if (repoErrors.length) {
    return (
      <WarningTooltip
        content={
          <div>{`${repoErrors.length} ${
            repoErrors.length === 1
              ? 'repository location failed to load'
              : 'repository locations failed to load'
          }`}</div>
        }
        position="right"
      >
        <Icon icon="warning-sign" iconSize={14} color={Colors.GOLD4} title="Warnings found" />
      </WarningTooltip>
    );
  }

  return null;
});
