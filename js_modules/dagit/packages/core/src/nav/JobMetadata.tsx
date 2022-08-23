import {gql, useQuery} from '@apollo/client';
import {Box, Button, ButtonLink, Colors, DialogFooter, Dialog, Table, Tag} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {DagsterTag} from '../runs/RunTag';
import {RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {SCHEDULE_SWITCH_FRAGMENT} from '../schedules/ScheduleSwitch';
import {SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitch';
import {RepoAddress} from '../workspace/types';

import {LatestRunTag} from './LatestRunTag';
import {ScheduleOrSensorTag} from './ScheduleOrSensorTag';
import {JobMetadataFragment as Job} from './types/JobMetadataFragment';
import {JobMetadataQuery, JobMetadataQueryVariables} from './types/JobMetadataQuery';
import {RunMetadataFragment} from './types/RunMetadataFragment';

interface Props {
  pipelineName: string;
  repoAddress: RepoAddress;
}

export const JobMetadata: React.FC<Props> = (props) => {
  const {pipelineName, repoAddress} = props;

  const {data} = useQuery<JobMetadataQuery, JobMetadataQueryVariables>(JOB_METADATA_QUERY, {
    variables: {
      runsFilter: {
        pipelineName,
        tags: [
          {
            key: DagsterTag.RepositoryLabelTag,
            value: `${repoAddress.name}@${repoAddress.location}`,
          },
        ],
      },
      params: {
        pipelineName,
        repositoryName: repoAddress.name,
        repositoryLocationName: repoAddress.location,
      },
    },
  });

  const job = React.useMemo(() => {
    if (data?.pipelineOrError && data.pipelineOrError.__typename === 'Pipeline') {
      return data.pipelineOrError;
    }
    return null;
  }, [data]);

  const runsForAssetScan = React.useMemo(() => {
    if (data?.pipelineRunsOrError && data.pipelineRunsOrError.__typename === 'Runs') {
      return data.pipelineRunsOrError.results;
    }
    return [];
  }, [data]);

  return (
    <>
      {job ? <JobScheduleOrSensorTag job={job} repoAddress={repoAddress} /> : null}
      <LatestRunTag pipelineName={pipelineName} repoAddress={repoAddress} />
      {runsForAssetScan ? <RelatedAssetsTag runs={runsForAssetScan} /> : null}
    </>
  );
};

const JobScheduleOrSensorTag: React.FC<{
  job: Job;
  repoAddress: RepoAddress;
}> = ({job, repoAddress}) => {
  const matchingSchedules = React.useMemo(() => {
    if (job?.__typename === 'Pipeline' && job.schedules.length) {
      return job.schedules;
    }
    return [];
  }, [job]);

  const matchingSensors = React.useMemo(() => {
    if (job?.__typename === 'Pipeline' && job.sensors.length) {
      return job.sensors;
    }
    return [];
  }, [job]);

  return (
    <ScheduleOrSensorTag
      schedules={matchingSchedules}
      sensors={matchingSensors}
      repoAddress={repoAddress}
    />
  );
};

const RelatedAssetsTag: React.FC<{runs: RunMetadataFragment[]}> = ({runs}) => {
  const [open, setOpen] = React.useState(false);

  const assetMap = {};
  runs.forEach((run) => {
    run.assets.forEach((asset) => {
      const assetKeyStr = asset.key.path.join('/');
      assetMap[assetKeyStr] = true;
    });
  });

  const keys = Object.keys(assetMap);
  if (keys.length === 0) {
    return null;
  }

  if (keys.length === 1) {
    const key = keys[0];
    return (
      <Tag icon="asset">
        Asset: <Link to={`/instance/assets/${key}`}>{key}</Link>
      </Tag>
    );
  }

  return (
    <>
      <Tag icon="asset">
        <ButtonLink
          color={Colors.Link}
          onClick={() => setOpen(true)}
        >{`View ${keys.length} assets`}</ButtonLink>
      </Tag>
      <Dialog
        title="Related assets"
        canOutsideClickClose
        canEscapeKeyClose
        isOpen={open}
        onClose={() => setOpen(false)}
        style={{maxWidth: '80%', minWidth: '500px', width: 'auto'}}
      >
        <Box padding={{bottom: 12}}>
          <Table>
            <tbody>
              {keys.map((key) => (
                <tr key={key}>
                  <td>
                    <Link
                      key={key}
                      to={`/instance/assets/${key}`}
                      style={{wordBreak: 'break-word'}}
                    >
                      {key}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Box>
        <DialogFooter>
          <Button intent="primary" onClick={() => setOpen(false)}>
            OK
          </Button>
        </DialogFooter>
      </Dialog>
    </>
  );
};

const RUN_METADATA_FRAGMENT = gql`
  fragment RunMetadataFragment on PipelineRun {
    id
    status
    assets {
      id
      key {
        path
      }
    }
    ...RunTimeFragment
  }
  ${RUN_TIME_FRAGMENT}
`;

const JOB_METADATA_FRAGMENT = gql`
  fragment JobMetadataFragment on Pipeline {
    id
    isJob
    name
    schedules {
      id
      mode
      ...ScheduleSwitchFragment
    }
    sensors {
      id
      targets {
        pipelineName
        mode
      }
      ...SensorSwitchFragment
    }
  }
  ${SCHEDULE_SWITCH_FRAGMENT}
  ${SENSOR_SWITCH_FRAGMENT}
`;

const JOB_METADATA_QUERY = gql`
  query JobMetadataQuery($params: PipelineSelector!, $runsFilter: RunsFilter!) {
    pipelineOrError(params: $params) {
      ... on Pipeline {
        id
        ...JobMetadataFragment
      }
    }
    pipelineRunsOrError(filter: $runsFilter, limit: 5) {
      ... on PipelineRuns {
        results {
          id
          ...RunMetadataFragment
        }
      }
    }
  }
  ${JOB_METADATA_FRAGMENT}
  ${RUN_METADATA_FRAGMENT}
`;
