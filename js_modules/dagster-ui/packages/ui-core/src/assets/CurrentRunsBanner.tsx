import {Alert, Box, Spinner} from '@dagster-io/ui-components';
import {BorderSetting, BorderSide} from '@dagster-io/ui-components/src/components/types';
import {Fragment} from 'react';
import {Link} from 'react-router-dom';

import {LiveDataForNode} from '../asset-graph/Utils';
import {titleForRun} from '../runs/RunUtils';
import {useStepLogs} from '../runs/StepLogsDialog';

export const CurrentRunsBanner = ({
  stepKey,
  liveData,
  border,
}: {
  liveData?: LiveDataForNode;
  border: BorderSide | BorderSetting;
  stepKey: string;
}) => {
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
                  {inProgressRunIds.length > 1 && (
                    <>
                      Runs <RunIdLinks ids={inProgressRunIds} /> are currently refreshing this
                      asset.
                    </>
                  )}
                  {inProgressRunIds.length === 1 && (
                    <>
                      Run <RunIdLinks ids={inProgressRunIds} /> is currently refreshing this asset.
                    </>
                  )}
                  {inProgressRunIds.length && unstartedRunIds.length ? ' ' : ''}
                  {unstartedRunIds.length > 1 && (
                    <>
                      Runs <RunIdLinks ids={unstartedRunIds} /> are queued and target this asset.
                    </>
                  )}
                  {unstartedRunIds.length === 1 && (
                    <>
                      Run <RunIdLinks ids={unstartedRunIds} /> is queued and targets this asset.
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

const RunIdLinks = ({ids}: {ids: string[]}) =>
  ids.length <= 4
    ? ids.map((id, idx) => (
        <Fragment key={id}>
          <Link to={`/runs/${id}`}>{titleForRun({id})}</Link>
          {idx < ids.length - 1 ? ', ' : ' '}
        </Fragment>
      ))
    : '';
