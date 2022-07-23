import {Colors, Icon} from '@dagster-io/ui';
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
        position="bottom"
        modifiers={{offset: {enabled: true, options: {offset: [0, 28]}}}}
      >
        <Icon name="warning" color={Colors.Yellow500} />
      </WarningTooltip>
    );
  }

  return null;
});
