import {Alert, Box} from '@dagster-io/ui-components';
import {
  BorderSide,
  BorderSetting,
  DirectionalSpacing,
} from '@dagster-io/ui-components/src/components/types';
import React from 'react';
import {Link} from 'react-router-dom';

import {AssetLatestInfoRunFragment} from '../asset-data/types/AssetLiveDataThread.types';
import {titleForRun} from '../runs/RunUtils';
import {useStepLogs} from '../runs/StepLogsDialog';

export const FailedRunSinceMaterializationBanner = ({
  run,
  stepKey,
  border,
  padding = {vertical: 16, left: 24, right: 12},
}: {
  run: AssetLatestInfoRunFragment | null;
  padding?: DirectionalSpacing;
  border?: BorderSide | BorderSetting;
  stepKey?: string;
}) => {
  const stepLogs = useStepLogs({runId: run?.id, stepKeys: stepKey ? [stepKey] : []});

  return (
    <>
      {stepLogs.dialog}
      {run && (
        <Box
          padding={padding}
          border={border}
          flex={{gap: 8, alignItems: 'center'}}
          style={{width: '100%'}}
        >
          <div style={{flex: 1}}>
            <Alert
              intent="error"
              title={
                <Box flex={{justifyContent: 'space-between'}}>
                  <div style={{fontWeight: 400}}>
                    Run <Link to={`/runs/${run.id}`}>{titleForRun(run)}</Link> failed to materialize
                    this asset.
                  </div>
                </Box>
              }
            />
          </div>
          {stepLogs.button}
        </Box>
      )}
    </>
  );
};
