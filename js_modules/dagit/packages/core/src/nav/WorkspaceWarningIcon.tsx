import * as React from 'react';

import {ColorsWIP} from '../ui/Colors';
import {IconWIP} from '../ui/Icon';
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
        <IconWIP name="warning" color={ColorsWIP.Yellow500} />
      </WarningTooltip>
    );
  }

  return null;
});
