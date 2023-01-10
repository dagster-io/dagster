import {useQuery} from '@apollo/client';
import {Box, Button, ButtonLink, Colors, DialogFooter, Dialog, Table, Tag} from '@dagster-io/ui';
import uniq from 'lodash/uniq';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {tokenForAssetKey} from '../asset-graph/Utils';
import {graphql} from '../graphql';
import {
  JobMetadataAssetNodeFragment,
  JobMetadataFragmentFragment,
  RunMetadataFragmentFragment,
} from '../graphql/graphql';
import {DagsterTag} from '../runs/RunTag';
import {repoAddressAsTag} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

import {LatestRunTag} from './LatestRunTag';
import {ScheduleOrSensorTag} from './ScheduleOrSensorTag';

type JobMetadata = {
  assetNodes: JobMetadataAssetNodeFragment[] | null;
  job: JobMetadataFragmentFragment | null;
  runsForAssetScan: RunMetadataFragmentFragment[];
};

export function useJobNavMetadata(repoAddress: RepoAddress, pipelineName: string) {
  const {data} = useQuery(JOB_METADATA_QUERY, {
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
      {metadata.runsForAssetScan ? (
        <RelatedAssetsTag relatedAssets={getRelatedAssets(metadata)} />
      ) : null}
    </>
  );
};

const JobScheduleOrSensorTag: React.FC<{
  job: JobMetadataFragmentFragment;
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
        <Box padding={{bottom: 12}}>
          <Table>
            <tbody>
              {relatedAssets.map((key) => (
                <tr key={key}>
                  <td>
                    <Link key={key} to={`/assets/${key}`} style={{wordBreak: 'break-word'}}>
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

const JOB_METADATA_QUERY = graphql(`
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
`);
