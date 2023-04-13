import {Alert, Box, Spinner} from '@dagster-io/ui';
import {BorderSetting} from '@dagster-io/ui/src/components/types';
import React from 'react';
import {Link} from 'react-router-dom';

import {LiveDataForNode} from '../asset-graph/Utils';
import {titleForRun} from '../runs/RunUtils';

export const CurrentRunsBanner: React.FC<{liveData?: LiveDataForNode; border: BorderSetting}> = ({
  liveData,
  border,
}) => {
  const {inProgressRunIds = [], unstartedRunIds = []} = liveData || {};

  if (inProgressRunIds.length === 0 && unstartedRunIds.length === 0) {
    return null;
  }
  return (
    <Box padding={{vertical: 16, left: 24, right: 12}} border={border}>
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
                {inProgressRunIds.length === 1 ? 'is' : 'are'} currently refreshing this asset.
              </>
            )}
            {unstartedRunIds.length > 0 && (
              <>
                {unstartedRunIds.map((id) => (
                  <React.Fragment key={id}>
                    Run <Link to={`/runs/${id}`}>{titleForRun({id})}</Link>
                  </React.Fragment>
                ))}{' '}
                {unstartedRunIds.length === 1 ? 'has' : 'have'} started and will refresh this asset.
              </>
            )}
          </div>
        }
      />
    </Box>
  );
};
