import {Alert, Box} from '@dagster-io/ui';
import {BorderSetting, DirectionalSpacing} from '@dagster-io/ui/src/components/types';
import React from 'react';
import {Link} from 'react-router-dom';

import {AssetLatestInfoRunFragment} from '../asset-graph/types/useLiveDataForAssetKeys.types';
import {titleForRun} from '../runs/RunUtils';

export const FailedRunSinceMaterializationBanner: React.FC<{
  run: AssetLatestInfoRunFragment | null;
  padding?: DirectionalSpacing;
  border?: BorderSetting;
}> = ({run, border, padding = {vertical: 16, left: 24, right: 12}}) => {
  if (run) {
    return (
      <Box padding={padding} border={border}>
        <Alert
          intent="error"
          title={
            <div style={{fontWeight: 400}}>
              Run <Link to={`/runs/${run.id}`}>{titleForRun(run)}</Link> failed to materialize this
              asset.
            </div>
          }
        />
      </Box>
    );
  }
  return null;
};
