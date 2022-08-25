import {useQuery, gql} from '@apollo/client';
import {Box, Colors, StyledTable, Tag, Tooltip} from '@dagster-io/ui';
import React from 'react';
import {Link} from 'react-router-dom';

import {useQueryRefreshAtInterval, FIFTEEN_SECONDS} from '../app/QueryRefresh';
import {timingStringForStatus} from '../runs/RunDetails';
import {RunStatusIndicator} from '../runs/RunStatusDots';
import {DagsterTag} from '../runs/RunTag';
import {RunTime, RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {RunStatus} from '../types/globalTypes';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

import {LatestRunTagQuery, LatestRunTagQueryVariables} from './types/LatestRunTagQuery';

const TIME_FORMAT = {showSeconds: true, showTimezone: false};

export const LatestRunTag: React.FC<{pipelineName: string; repoAddress: RepoAddress}> = ({
  pipelineName,
  repoAddress,
}) => {
  const lastRunQuery = useQuery<LatestRunTagQuery, LatestRunTagQueryVariables>(
    LATEST_RUN_TAG_QUERY,
    {
      variables: {
        runsFilter: {
          pipelineName,
          tags: [
            {
              key: DagsterTag.RepositoryLabelTag,
              value: repoAddressAsString(repoAddress),
            },
          ],
        },
      },
      notifyOnNetworkStatusChange: true,
    },
  );

  useQueryRefreshAtInterval(lastRunQuery, FIFTEEN_SECONDS);

  const run = React.useMemo(() => {
    const runsOrError = lastRunQuery.data?.pipelineRunsOrError;
    if (runsOrError && runsOrError.__typename === 'Runs') {
      return runsOrError.results[0] || null;
    }
    return null;
  }, [lastRunQuery]);

  if (!run) {
    return null;
  }

  const stats = {start: run.startTime, end: run.endTime, status: run.status};
  const intent = () => {
    switch (run.status) {
      case RunStatus.SUCCESS:
        return 'success';
      case RunStatus.CANCELED:
      case RunStatus.CANCELING:
      case RunStatus.FAILURE:
        return 'danger';
      default:
        return 'none';
    }
  };

  return (
    <Tag intent={intent()}>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
        <RunStatusIndicator status={run.status} size={10} />
        Latest run:
        {stats ? (
          <Tooltip
            placement="bottom"
            content={
              <StyledTable>
                <tbody>
                  <tr>
                    <td style={{color: Colors.Gray300}}>
                      <Box padding={{right: 16}}>Started</Box>
                    </td>
                    <td>
                      {stats.start ? (
                        <TimestampDisplay timestamp={stats.start} timeFormat={TIME_FORMAT} />
                      ) : (
                        timingStringForStatus(stats.status)
                      )}
                    </td>
                  </tr>
                  <tr>
                    <td style={{color: Colors.Gray300}}>Ended</td>
                    <td>
                      {stats.end ? (
                        <TimestampDisplay timestamp={stats.end} timeFormat={TIME_FORMAT} />
                      ) : (
                        timingStringForStatus(stats.status)
                      )}
                    </td>
                  </tr>
                </tbody>
              </StyledTable>
            }
          >
            <Link to={`/instance/runs/${run.id}`}>
              <RunTime run={run} />
            </Link>
          </Tooltip>
        ) : null}
      </Box>
    </Tag>
  );
};

const LATEST_RUN_TAG_QUERY = gql`
  query LatestRunTagQuery($runsFilter: RunsFilter) {
    pipelineRunsOrError(filter: $runsFilter, limit: 1) {
      ... on PipelineRuns {
        results {
          id
          status
          ...RunTimeFragment
        }
      }
    }
  }
  ${RUN_TIME_FRAGMENT}
`;
