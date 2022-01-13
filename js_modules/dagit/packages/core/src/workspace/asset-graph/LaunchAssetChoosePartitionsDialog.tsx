import {gql, useApolloClient} from '@apollo/client';
import {
  DialogWIP,
  DialogHeader,
  DialogBody,
  Box,
  Subheading,
  ButtonWIP,
  ButtonLink,
  DialogFooter,
} from '@dagster-io/ui';
import {flatten, pick} from 'lodash';
import React from 'react';
import {useHistory} from 'react-router-dom';
import * as yaml from 'yaml';

import {AppContext} from '../../app/AppContext';
import {SharedToaster} from '../../app/DomUtils';
import {displayNameForAssetKey} from '../../app/Util';
import {PartitionHealthSummary, usePartitionHealthData} from '../../assets/PartitionHealthSummary';
import {CONFIG_PARTITION_SELECTION_QUERY} from '../../launchpad/ConfigEditorConfigPicker';
import {
  ConfigPartitionSelectionQuery,
  ConfigPartitionSelectionQueryVariables,
} from '../../launchpad/types/ConfigPartitionSelectionQuery';
import {PartitionRangeInput} from '../../partitions/PartitionRangeInput';
import {
  LAUNCH_PARTITION_BACKFILL_MUTATION,
  messageForLaunchBackfillError,
} from '../../partitions/PartitionsBackfill';
import {
  LaunchPartitionBackfill,
  LaunchPartitionBackfillVariables,
} from '../../partitions/types/LaunchPartitionBackfill';
import {handleLaunchResult, LAUNCH_PIPELINE_EXECUTION_MUTATION} from '../../runs/RunUtils';
import {
  LaunchPipelineExecution,
  LaunchPipelineExecutionVariables,
} from '../../runs/types/LaunchPipelineExecution';
import {RepoAddress} from '../types';

export const LaunchAssetChoosePartitionsDialog: React.FC<{
  open: boolean;
  setOpen: (open: boolean) => void;
  repoAddress: RepoAddress;
  assetJobName: string;
  assets: {assetKey: {path: string[]}; opName: string | null; partitionDefinition: string | null}[];
}> = ({open, setOpen, assets, repoAddress, assetJobName}) => {
  const data = usePartitionHealthData(assets[0].assetKey);
  const [selected, setSelected] = React.useState<string[]>([]);
  const [previewCount, setPreviewCount] = React.useState(4);
  const [launching, setLaunching] = React.useState(false);

  const setMostRecent = () => setSelected([data.keys[data.keys.length - 1]]);
  const setAll = () => setSelected([...data.keys]);
  const setMissing = () =>
    setSelected(
      flatten(
        data.spans
          .filter((s) => s.status === false)
          .map((s) => data.keys.slice(s.startIdx, s.endIdx + 1)),
      ),
    );

  React.useEffect(() => {
    setSelected([data.keys[data.keys.length - 1]]);
  }, [data.keys]);

  const title = `Launch runs to materialize ${
    assets.length > 1 ? `${assets.length} assets` : displayNameForAssetKey(assets[0].assetKey)
  }`;

  const client = useApolloClient();
  const {basePath} = React.useContext(AppContext);
  const history = useHistory();

  const onLaunch = async () => {
    setLaunching(true);

    // Find the partition set name. This seems like a bit of a hack, unclear
    // how it would work if there were two different partition spaces in the asset job
    const {data: partitionSetsData} = await client.query<any, any>({
      query: ASSET_JOB_PARTITION_SETS_QUERY,
      variables: {
        repositoryLocationName: repoAddress.location,
        repositoryName: repoAddress.name,
        pipelineName: assetJobName,
      },
    });

    const partitionSet =
      partitionSetsData.partitionSetsOrError.__typename === 'PartitionSets'
        ? partitionSetsData.partitionSetsOrError.results[0]
        : undefined;

    if (selected.length === 1) {
      const {data: tagAndConfigData} = await client.query<
        ConfigPartitionSelectionQuery,
        ConfigPartitionSelectionQueryVariables
      >({
        query: CONFIG_PARTITION_SELECTION_QUERY,
        variables: {
          repositorySelector: {
            repositoryLocationName: repoAddress.location,
            repositoryName: repoAddress.name,
          },
          partitionSetName: partitionSet.name,
          partitionName: selected[0],
        },
      });

      if (
        !tagAndConfigData ||
        !tagAndConfigData.partitionSetOrError ||
        tagAndConfigData.partitionSetOrError.__typename !== 'PartitionSet' ||
        !tagAndConfigData.partitionSetOrError.partition
      ) {
        return;
      }

      const {partition} = tagAndConfigData.partitionSetOrError;

      let tags: {key: string; value: string}[] = [];
      if (partition.tagsOrError.__typename !== 'PythonError') {
        tags = [...partition.tagsOrError.results];
      }
      let runConfigData = {};
      if (partition.runConfigOrError.__typename !== 'PythonError') {
        runConfigData = yaml.parse(partition.runConfigOrError.yaml || '') || {};
      }

      const launchResult = await client.mutate<
        LaunchPipelineExecution,
        LaunchPipelineExecutionVariables
      >({
        mutation: LAUNCH_PIPELINE_EXECUTION_MUTATION,
        variables: {
          executionParams: {
            runConfigData,
            mode: partition.mode,
            stepKeys: assets.map((a) => a.opName!),
            selector: {
              repositoryLocationName: repoAddress.location,
              repositoryName: repoAddress.name,
              jobName: assetJobName,
            },
            executionMetadata: {
              tags: tags.map((t) => pick(t, ['key', 'value'])),
            },
          },
        },
      });

      handleLaunchResult(basePath, assetJobName, launchResult, {});
    } else {
      const launchBackfillResult = await client.mutate<
        LaunchPartitionBackfill,
        LaunchPartitionBackfillVariables
      >({
        mutation: LAUNCH_PARTITION_BACKFILL_MUTATION,
        variables: {
          backfillParams: {
            selector: {
              partitionSetName: partitionSet.name,
              repositorySelector: {
                repositoryLocationName: repoAddress.location,
                repositoryName: repoAddress.name,
              },
            },
            partitionNames: selected,
            reexecutionSteps: assets.map((a) => a.opName!),
            fromFailure: false,
            tags: [],
          },
        },
      });

      if (
        launchBackfillResult.data?.launchPartitionBackfill.__typename === 'LaunchBackfillSuccess'
      ) {
        history.push('/instance/backfills');
      } else {
        setLaunching(false);
        SharedToaster.show({
          message: messageForLaunchBackfillError(launchBackfillResult.data),
          icon: 'error',
          intent: 'danger',
        });
      }
    }
  };

  return (
    <DialogWIP
      style={{width: 700}}
      isOpen={open}
      canEscapeKeyClose
      canOutsideClickClose
      onClose={() => setOpen(false)}
    >
      <DialogHeader icon="layers" label={title} />
      <DialogBody>
        <Box flex={{direction: 'column', gap: 8}}>
          <Subheading style={{flex: 1}}>Partition Keys</Subheading>
          <Box flex={{direction: 'row', gap: 8, alignItems: 'baseline'}}>
            <Box flex={{direction: 'column'}} style={{flex: 1}}>
              <PartitionRangeInput
                value={selected}
                onChange={setSelected}
                partitionNames={data.keys}
              />
            </Box>
            <ButtonWIP small onClick={setMostRecent}>
              Most Recent
            </ButtonWIP>
            <ButtonWIP small onClick={setMissing}>
              Missing
            </ButtonWIP>
            <ButtonWIP small onClick={setAll}>
              All
            </ButtonWIP>
          </Box>
        </Box>
        <Box
          flex={{direction: 'column', gap: 8}}
          style={{marginTop: 16, overflowY: 'auto', overflowX: 'visible', maxHeight: '50vh'}}
        >
          {assets.slice(0, previewCount).map((a) => (
            <PartitionHealthSummary
              assetKey={a.assetKey}
              showAssetKey
              key={displayNameForAssetKey(a.assetKey)}
              selected={selected}
            />
          ))}
          {previewCount < assets.length ? (
            <Box margin={{vertical: 8}}>
              <ButtonLink onClick={() => setPreviewCount(assets.length)}>
                Show {assets.length - previewCount} more previews
              </ButtonLink>
            </Box>
          ) : undefined}
        </Box>
      </DialogBody>
      <DialogFooter>
        <ButtonWIP intent="none" onClick={() => setOpen(false)}>
          Cancel
        </ButtonWIP>
        <ButtonWIP intent="primary" onClick={onLaunch}>
          {launching
            ? 'Launching...'
            : selected.length !== 1
            ? `Launch ${selected.length} Run Backfill`
            : `Launch 1 Run`}
        </ButtonWIP>
      </DialogFooter>
    </DialogWIP>
  );
};

const ASSET_JOB_PARTITION_SETS_QUERY = gql`
  query AssetJobPartitionSetsQuery(
    $pipelineName: String!
    $repositoryName: String!
    $repositoryLocationName: String!
  ) {
    partitionSetsOrError(
      pipelineName: $pipelineName
      repositorySelector: {
        repositoryName: $repositoryName
        repositoryLocationName: $repositoryLocationName
      }
    ) {
      __typename
      ... on PartitionSets {
        __typename
        results {
          id
          name
          mode
          solidSelection
        }
      }
    }
  }
`;
