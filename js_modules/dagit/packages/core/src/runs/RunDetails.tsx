import {gql} from '@apollo/client';
import {
  ButtonWIP,
  ColorsWIP,
  DialogBody,
  DialogFooter,
  DialogWIP,
  Group,
  HighlightedCodeBlock,
  IconWIP,
  MetadataTable,
  Tooltip,
} from '@dagster-io/ui';
import * as React from 'react';
import * as yaml from 'yaml';

import {AppContext} from '../app/AppContext';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {RunStatus} from '../types/globalTypes';

import {RunTags} from './RunTags';
import {TimeElapsed} from './TimeElapsed';
import {RunDetailsFragment} from './types/RunDetailsFragment';
import {RunFragment} from './types/RunFragment';

export const timingStringForStatus = (status?: RunStatus) => {
  switch (status) {
    case RunStatus.QUEUED:
      return 'Queued';
    case RunStatus.CANCELED:
      return 'Canceled';
    case RunStatus.CANCELING:
      return 'Canceling…';
    case RunStatus.FAILURE:
      return 'Failed';
    case RunStatus.NOT_STARTED:
      return 'Waiting to start…';
    case RunStatus.STARTED:
      return 'Started…';
    case RunStatus.STARTING:
      return 'Starting…';
    case RunStatus.SUCCESS:
      return 'Succeeded';
    default:
      return 'None';
  }
};

const LoadingOrValue: React.FC<{
  loading: boolean;
  children: () => React.ReactNode;
}> = ({loading, children}) =>
  loading ? <div style={{color: ColorsWIP.Gray400}}>Loading…</div> : <div>{children()}</div>;

const TIME_FORMAT = {showSeconds: true, showTimezone: false};

export const RunDetails: React.FC<{
  loading: boolean;
  run: RunDetailsFragment | undefined;
}> = ({loading, run}) => {
  return (
    <MetadataTable
      spacing={0}
      rows={[
        {
          key: 'Started',
          value: (
            <LoadingOrValue loading={loading}>
              {() => {
                if (run?.stats.__typename === 'RunStatsSnapshot' && run.stats.startTime) {
                  return (
                    <TimestampDisplay timestamp={run.stats.startTime} timeFormat={TIME_FORMAT} />
                  );
                }
                return (
                  <div style={{color: ColorsWIP.Gray400}}>{timingStringForStatus(run?.status)}</div>
                );
              }}
            </LoadingOrValue>
          ),
        },
        {
          key: 'Ended',
          value: (
            <LoadingOrValue loading={loading}>
              {() => {
                if (run?.stats.__typename === 'RunStatsSnapshot' && run.stats.endTime) {
                  return (
                    <TimestampDisplay timestamp={run.stats.endTime} timeFormat={TIME_FORMAT} />
                  );
                }
                return (
                  <div style={{color: ColorsWIP.Gray400}}>{timingStringForStatus(run?.status)}</div>
                );
              }}
            </LoadingOrValue>
          ),
        },
        {
          key: 'Duration',
          value: (
            <LoadingOrValue loading={loading}>
              {() => {
                if (run?.stats.__typename === 'RunStatsSnapshot' && run.stats.startTime) {
                  return (
                    <TimeElapsed startUnix={run.stats.startTime} endUnix={run.stats.endTime} />
                  );
                }
                return (
                  <div style={{color: ColorsWIP.Gray400}}>{timingStringForStatus(run?.status)}</div>
                );
              }}
            </LoadingOrValue>
          ),
        },
      ]}
    />
  );
};

export const RunConfigDialog: React.FC<{run: RunFragment; isJob: boolean}> = ({run, isJob}) => {
  const [showDialog, setShowDialog] = React.useState(false);
  const {rootServerURI} = React.useContext(AppContext);
  const runConfigYaml = yaml.stringify(run.runConfig) || '';
  return (
    <div>
      <Group direction="row" spacing={8}>
        <ButtonWIP icon={<IconWIP name="tag" />} onClick={() => setShowDialog(true)}>
          View tags and config
        </ButtonWIP>
        <Tooltip content="Loadable in dagit-debug" position="bottom-right">
          <ButtonWIP
            icon={<IconWIP name="download_for_offline" />}
            onClick={() => window.open(`${rootServerURI}/download_debug/${run.runId}`)}
          >
            Debug file
          </ButtonWIP>
        </Tooltip>
      </Group>
      <DialogWIP
        isOpen={showDialog}
        onClose={() => setShowDialog(false)}
        style={{width: '800px'}}
        title="Run configuration"
      >
        <DialogBody>
          <Group direction="column" spacing={20}>
            <Group direction="column" spacing={12}>
              <div style={{fontSize: '16px', fontWeight: 600}}>Tags</div>
              <div>
                <RunTags tags={run.tags} mode={isJob ? null : run.mode} />
              </div>
            </Group>
            <Group direction="column" spacing={12}>
              <div style={{fontSize: '16px', fontWeight: 600}}>Config</div>
              <HighlightedCodeBlock value={runConfigYaml} language="yaml" />
            </Group>
          </Group>
        </DialogBody>
        <DialogFooter>
          <ButtonWIP onClick={() => setShowDialog(false)} intent="primary">
            OK
          </ButtonWIP>
        </DialogFooter>
      </DialogWIP>
    </div>
  );
};

export const RUN_DETAILS_FRAGMENT = gql`
  fragment RunDetailsFragment on Run {
    id
    stats {
      ... on RunStatsSnapshot {
        id
        endTime
        startTime
      }
    }
    status
  }
`;
