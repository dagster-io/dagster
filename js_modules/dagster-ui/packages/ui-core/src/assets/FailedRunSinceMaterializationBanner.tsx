import {Alert, Box, Mono} from '@dagster-io/ui-components';
import {
  BorderSetting,
  BorderSide,
  DirectionalSpacing,
} from '@dagster-io/ui-components/src/components/types';
import {Link} from 'react-router-dom';

import {AssetLatestInfoRunFragment} from '../asset-data/types/AssetBaseDataQueries.types';
import {RunStatus} from '../graphql/types';
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

  const alertIntent = run?.status === RunStatus.CANCELED ? 'warning' : 'error';

  const content = () => {
    if (run?.status === RunStatus.CANCELED) {
      return (
        <>
          Run{' '}
          <Link to={`/runs/${run.id}`}>
            <Mono style={{fontWeight: 600}}>{titleForRun(run)}</Mono>
          </Link>{' '}
          was canceled, and did not materialize this asset.
        </>
      );
    }

    if (run?.status === RunStatus.FAILURE) {
      return (
        <>
          Run{' '}
          <Link to={`/runs/${run.id}`}>
            <Mono style={{fontWeight: 600}}>{titleForRun(run)}</Mono>
          </Link>{' '}
          failed, and did not materialize this asset.
        </>
      );
    }

    return null;
  };

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
            <Alert intent={alertIntent} title={content()} />
          </div>
          {stepLogs.button}
        </Box>
      )}
    </>
  );
};
