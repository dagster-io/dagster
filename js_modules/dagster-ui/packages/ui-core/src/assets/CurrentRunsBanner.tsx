import {Alert, Box, Spinner} from '@dagster-io/ui-components';
import {BorderSide, BorderSetting} from '@dagster-io/ui-components/src/components/types';
import React from 'react';
import {Link} from 'react-router-dom';

import {LiveDataForNode} from '../asset-graph/Utils';
import {titleForRun} from '../runs/RunUtils';
import {useStepLogs} from '../runs/StepLogsDialog';

export const CurrentRunsBanner: React.FC<{
  liveData?: LiveDataForNode;
  border: BorderSide | BorderSetting;
  stepKey: string;
}> = ({stepKey, liveData, border}) => {
  const {inProgressRunIds = [], unstartedRunIds = []} = liveData || {};
  const firstRunId = inProgressRunIds[0] || unstartedRunIds[0];
  const stepLogs = useStepLogs({runId: firstRunId, stepKeys: [stepKey]});

  return (
    <>
      {stepLogs.dialog}
      {firstRunId && (
        <Box
          padding={{vertical: 16, left: 24, right: 12}}
          border={border}
          flex={{gap: 8, alignItems: 'center'}}
          style={{width: '100%'}}
        >
          <div style={{flex: 1}}>
            <Alert
              intent="info"
              icon={<Spinner purpose="body-text" />}
              title={
                <div style={{fontWeight: 400}}>
                  {inProgressRunIds.length > 0 && (
                    <>
                      {inProgressRunIds.map((id) => (
                        <React.Fragment key={id}>
                          Run <Link to={`/runs/${id}`}>{titleForRun({id})}</Link>
                        </React.Fragment>
                      ))}{' '}
                      {inProgressRunIds.length === 1 ? 'is' : 'are'} currently refreshing this
                      asset.
                    </>
                  )}
                  {unstartedRunIds.length > 0 && (
                    <>
                      {unstartedRunIds.map((id) => (
                        <React.Fragment key={id}>
                          Run <Link to={`/runs/${id}`}>{titleForRun({id})}</Link>
                        </React.Fragment>
                      ))}{' '}
                      {unstartedRunIds.length === 1 ? 'has' : 'have'} started and will refresh this
                      asset.
                    </>
                  )}
                </div>
              }
            />
          </div>
          {stepLogs.button}
        </Box>
      )}
    </>
  );
};
