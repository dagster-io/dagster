import {gql, useQuery} from '@apollo/client';
import {Box, Button, ButtonLink, Colors, DialogFooter, Dialog, Table, Tag} from '@dagster-io/ui';
import uniq from 'lodash/uniq';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {tokenForAssetKey} from '../asset-graph/Utils';
import {DagsterTag} from '../runs/RunTag';
import {RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {SCHEDULE_SWITCH_FRAGMENT} from '../schedules/ScheduleSwitch';
import {SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitch';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

import {LatestRunTag} from './LatestRunTag';
import {ScheduleOrSensorTag} from './ScheduleOrSensorTag';
import {JobMetadataFragment as Job} from './types/JobMetadataFragment';
import {
  JobMetadataQuery,
  JobMetadataQueryVariables,
  JobMetadataQuery_assetNodes,
  JobMetadataQuery_pipelineOrError_Pipeline,
  JobMetadataQuery_pipelineRunsOrError_Runs_results,
} from './types/JobMetadataQuery';

type JobMetadata = {
  assetNodes: JobMetadataQuery_assetNodes[] | null;
  job: JobMetadataQuery_pipelineOrError_Pipeline | null;
  runsForAssetScan: JobMetadataQuery_pipelineRunsOrError_Runs_results[];
};

export function useJobNavMetadata(repoAddress: RepoAddress, pipelineName: string) {
  const {data} = useQuery<JobMetadataQuery, JobMetadataQueryVariables>(JOB_METADATA_QUERY, {
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
      params: {
        pipelineName,
        repositoryName: repoAddress.name,
        repositoryLocationName: repoAddress.location,
      },
    },
  });

  return React.useMemo<JobMetadata>(() => {
    return {
      assetNodes: data?.assetNodes || null,
      job:
        data?.pipelineOrError && data.pipelineOrError.__typename === 'Pipeline'
          ? data.pipelineOrError
          : null,
      runsForAssetScan:
        data?.pipelineRunsOrError && data.pipelineRunsOrError.__typename === 'Runs'
          ? data.pipelineRunsOrError.results
          : [],
    };
  }, [data]);
}

interface Props {
  pipelineName: string;
  repoAddress: RepoAddress;
  metadata: JobMetadata;
}

export const JobMetadata: React.FC<Props> = (props) => {
  const {metadata, pipelineName, repoAddress} = props;

  return (
    <>
      {metadata.job ? (
        <JobScheduleOrSensorTag job={metadata.job} repoAddress={repoAddress} />
      ) : null}
      <LatestRunTag pipelineName={pipelineName} repoAddress={repoAddress} />
      {metadata.runsForAssetScan ? (
        <RelatedAssetsTag relatedAssets={getRelatedAssets(metadata)} />
      ) : null}
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

function getRelatedAssets(metadata: JobMetadata) {
  if (metadata.assetNodes) {
    return metadata.assetNodes.map((node) => tokenForAssetKey(node.assetKey));
  }

  return uniq(
    metadata.runsForAssetScan.flatMap((r) => r.assets.map((a) => tokenForAssetKey(a.key))),
  );
}

const RelatedAssetsTag: React.FC<{relatedAssets: string[]}> = ({relatedAssets}) => {
  const [open, setOpen] = React.useState(false);

  if (relatedAssets.length === 0) {
    return null;
  }

  if (relatedAssets.length === 1) {
    const key = relatedAssets[0];
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
        >{`View ${relatedAssets.length} assets`}</ButtonLink>
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
              {relatedAssets.map((key) => (
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
    assetNodes(pipeline: $params) {
      id
      assetKey {
        path
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
