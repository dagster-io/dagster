import {gql, useQuery} from '@apollo/client';
import {Box, Button, ButtonLink, Colors, DialogFooter, Dialog, Tag} from '@dagster-io/ui';
import uniq from 'lodash/uniq';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {tokenForAssetKey} from '../asset-graph/Utils';
import {AutomaterializeDaemonStatusTag} from '../assets/AutomaterializeDaemonStatusTag';
import {DagsterTag} from '../runs/RunTag';
import {RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {SCHEDULE_SWITCH_FRAGMENT} from '../schedules/ScheduleSwitch';
import {SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitch';
import {repoAddressAsTag} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

import {LatestRunTag} from './LatestRunTag';
import {ScheduleOrSensorTag} from './ScheduleOrSensorTag';
import {
  JobMetadataAssetNodeFragment,
  JobMetadataFragment,
  JobMetadataQuery,
  JobMetadataQueryVariables,
  RunMetadataFragment,
} from './types/JobMetadata.types';

type JobMetadata = {
  assetNodes: JobMetadataAssetNodeFragment[] | null;
  job: JobMetadataFragment | null;
  runsForAssetScan: RunMetadataFragment[];
};

function useJobNavMetadata(repoAddress: RepoAddress, pipelineName: string) {
  const {data} = useQuery<JobMetadataQuery, JobMetadataQueryVariables>(JOB_METADATA_QUERY, {
    variables: {
      runsFilter: {
        pipelineName,
        tags: [
          {
            key: DagsterTag.RepositoryLabelTag,
            value: repoAddressAsTag(repoAddress),
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
}

export const JobMetadata: React.FC<Props> = (props) => {
  const {pipelineName, repoAddress} = props;
  const metadata = useJobNavMetadata(repoAddress, pipelineName);

  return (
    <>
      {metadata.job ? (
        <JobScheduleOrSensorTag job={metadata.job} repoAddress={repoAddress} />
      ) : null}
      <LatestRunTag pipelineName={pipelineName} repoAddress={repoAddress} />
      {metadata.assetNodes && metadata.assetNodes.some((a) => !!a.autoMaterializePolicy) && (
        <AutomaterializeDaemonStatusTag />
      )}
      {metadata.runsForAssetScan ? (
        <RelatedAssetsTag relatedAssets={getRelatedAssets(metadata)} />
      ) : null}
    </>
  );
};

const JobScheduleOrSensorTag: React.FC<{
  job: JobMetadataFragment;
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
        Asset: <Link to={`/assets/${key}`}>{key}</Link>
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
        {relatedAssets.map((key, ii) => (
          <Box
            key={key}
            padding={{vertical: 12, horizontal: 20}}
            border={
              ii < relatedAssets.length - 1
                ? {side: 'bottom', width: 1, color: Colors.KeylineGray}
                : null
            }
          >
            <Link key={key} to={`/assets/${key}`} style={{wordBreak: 'break-word'}}>
              {key}
            </Link>
          </Box>
        ))}
        <DialogFooter topBorder>
          <Button intent="primary" onClick={() => setOpen(false)}>
            OK
          </Button>
        </DialogFooter>
      </Dialog>
    </>
  );
};

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
      ...JobMetadataAssetNode
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

  fragment JobMetadataAssetNode on AssetNode {
    id
    autoMaterializePolicy {
      policyType
    }
    assetKey {
      path
    }
  }

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

  ${SCHEDULE_SWITCH_FRAGMENT}
  ${SENSOR_SWITCH_FRAGMENT}
  ${RUN_TIME_FRAGMENT}
`;
