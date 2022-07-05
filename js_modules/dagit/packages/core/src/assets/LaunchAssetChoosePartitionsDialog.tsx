import {gql, useApolloClient, useQuery} from '@apollo/client';
import {
  Dialog,
  DialogHeader,
  DialogBody,
  Box,
  Subheading,
  Button,
  ButtonLink,
  DialogFooter,
  Alert,
} from '@dagster-io/ui';
import reject from 'lodash/reject';
import React from 'react';
import {useHistory} from 'react-router-dom';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {PartitionHealthSummary, usePartitionHealthData} from '../assets/PartitionHealthSummary';
import {AssetKey} from '../assets/types';
import {LAUNCH_PARTITION_BACKFILL_MUTATION} from '../instance/BackfillUtils';
import {
  LaunchPartitionBackfill,
  LaunchPartitionBackfillVariables,
} from '../instance/types/LaunchPartitionBackfill';
import {CONFIG_PARTITION_SELECTION_QUERY} from '../launchpad/ConfigEditorConfigPicker';
import {useLaunchWithTelemetry} from '../launchpad/LaunchRootExecutionButton';
import {
  ConfigPartitionSelectionQuery,
  ConfigPartitionSelectionQueryVariables,
} from '../launchpad/types/ConfigPartitionSelectionQuery';
import {
  assembleIntoSpans,
  PartitionRangeInput,
  stringForSpan,
} from '../partitions/PartitionRangeInput';
import {showBackfillErrorToast, showBackfillSuccessToast} from '../partitions/PartitionsBackfill';
import {RepoAddress} from '../workspace/types';

import {executionParamsForAssetJob} from './LaunchAssetExecutionButton';
import {RunningBackfillsNotice} from './RunningBackfillsNotice';
import {
  AssetJobPartitionSetsQuery,
  AssetJobPartitionSetsQueryVariables,
} from './types/AssetJobPartitionSetsQuery';

interface Props {
  open: boolean;
  setOpen: (open: boolean) => void;
  repoAddress: RepoAddress;
  assetJobName: string;
  assets: {assetKey: AssetKey; opNames: string[]; partitionDefinition: string | null}[];
  upstreamAssetKeys: AssetKey[]; // single layer of upstream dependencies
}

export const LaunchAssetChoosePartitionsDialog: React.FC<Props> = (props) => {
  const title = `Launch runs to materialize ${
    props.assets.length > 1
      ? `${props.assets.length} assets`
      : displayNameForAssetKey(props.assets[0].assetKey)
  }`;

  return (
    <Dialog
      style={{width: 700}}
      isOpen={props.open}
      canEscapeKeyClose
      canOutsideClickClose
      onClose={() => props.setOpen(false)}
    >
      <DialogHeader icon="layers" label={title} />
      <LaunchAssetChoosePartitionsDialogBody {...props} />
    </Dialog>
  );
};

// Note: This dialog loads a lot of data - the body is broken into a separate
// component so we can be *sure* the hooks won't load data until it's opened.
// (<Dialog> does not render it's children until open=true)
//
// Additionally, we want the dialog to reset when it's closed and re-opened so
// that partition health, etc. is up-to-date.
//
const LaunchAssetChoosePartitionsDialogBody: React.FC<Props> = ({
  setOpen,
  assets,
  repoAddress,
  assetJobName,
  upstreamAssetKeys,
}) => {
  const data = usePartitionHealthData(assets.map((a) => a.assetKey));
  const upstreamData = usePartitionHealthData(upstreamAssetKeys);

  const allKeys = data[0] ? data[0].keys : [];
  const mostRecentKey = allKeys[allKeys.length - 1];

  const [selected, setSelected] = React.useState<string[]>([]);
  const [previewCount, setPreviewCount] = React.useState(4);
  const [launching, setLaunching] = React.useState(false);

  const setMostRecent = () => setSelected([mostRecentKey]);
  const setAll = () => setSelected([...allKeys]);
  const setMissing = () =>
    setSelected(allKeys.filter((key) => data.every((d) => !d.statusByPartition[key])));

  React.useEffect(() => {
    setSelected([mostRecentKey]);
  }, [mostRecentKey]);

  const client = useApolloClient();
  const history = useHistory();
  const launchWithTelemetry = useLaunchWithTelemetry();

  // Find the partition set name. This seems like a bit of a hack, unclear
  // how it would work if there were two different partition spaces in the asset job
  const {data: partitionSetsData} = useQuery<
    AssetJobPartitionSetsQuery,
    AssetJobPartitionSetsQueryVariables
  >(ASSET_JOB_PARTITION_SETS_QUERY, {
    variables: {
      repositoryLocationName: repoAddress.location,
      repositoryName: repoAddress.name,
      pipelineName: assetJobName,
    },
  });

  const partitionSet =
    partitionSetsData?.partitionSetsOrError.__typename === 'PartitionSets'
      ? partitionSetsData.partitionSetsOrError.results[0]
      : undefined;

  const onLaunch = async () => {
    setLaunching(true);

    if (!partitionSet) {
      const error =
        partitionSetsData?.partitionSetsOrError.__typename === 'PythonError'
          ? partitionSetsData.partitionSetsOrError
          : {message: 'No details provided.'};

      setLaunching(false);
      showCustomAlert({
        title: `Unable to find partition set on ${assetJobName}`,
        body: <PythonErrorInfo error={error} />,
      });
      return;
    }

    if (selected.length === 1) {
      const {data: tagAndConfigData} = await client.query<
        ConfigPartitionSelectionQuery,
        ConfigPartitionSelectionQueryVariables
      >({
        query: CONFIG_PARTITION_SELECTION_QUERY,
        fetchPolicy: 'network-only',
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

      if (partition.tagsOrError.__typename === 'PythonError') {
        setLaunching(false);
        showCustomAlert({
          title: 'Unable to load tags',
          body: <PythonErrorInfo error={partition.tagsOrError} />,
        });
        return;
      }
      if (partition.runConfigOrError.__typename === 'PythonError') {
        setLaunching(false);
        showCustomAlert({
          title: 'Unable to load tags',
          body: <PythonErrorInfo error={partition.runConfigOrError} />,
        });
        return;
      }

      const tags = [...partition.tagsOrError.results];
      const runConfigData = partition.runConfigOrError.yaml || '';

      const result = await launchWithTelemetry(
        {
          executionParams: {
            ...executionParamsForAssetJob(repoAddress, assetJobName, assets, tags),
            runConfigData,
            mode: partition.mode,
          },
        },
        'toast',
      );

      setLaunching(false);
      if (result?.launchPipelineExecution.__typename === 'LaunchRunSuccess') {
        setOpen(false);
      }
    } else {
      const {data: launchBackfillData} = await client.mutate<
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
            reexecutionSteps: assets.map((a) => a.opNames).flat(),
            fromFailure: false,
            tags: [],
          },
        },
      });

      setLaunching(false);

      if (launchBackfillData?.launchPartitionBackfill.__typename === 'LaunchBackfillSuccess') {
        showBackfillSuccessToast(history, launchBackfillData?.launchPartitionBackfill.backfillId);
        setOpen(false);
      } else {
        showBackfillErrorToast(launchBackfillData);
      }
    }
  };

  const upstreamUnavailable = (key: string) =>
    upstreamData.length > 0 &&
    upstreamData.some((a) => a.keys.includes(key) && !a.statusByPartition[key]);

  const upstreamUnavailableSpans = assembleIntoSpans(selected, upstreamUnavailable).filter(
    (s) => s.status === true,
  );
  const onRemoveUpstreamUnavailable = () => {
    setSelected(reject(selected, upstreamUnavailable));
  };

  return (
    <>
      <DialogBody>
        <Box flex={{direction: 'column', gap: 8}}>
          <Subheading style={{flex: 1}}>Partition Keys</Subheading>
          <Box flex={{direction: 'row', gap: 8, alignItems: 'baseline'}}>
            <Box flex={{direction: 'column'}} style={{flex: 1}}>
              <PartitionRangeInput
                value={selected}
                onChange={setSelected}
                partitionNames={allKeys}
              />
            </Box>
            <Button small onClick={setMostRecent}>
              Most Recent
            </Button>
            <Button small onClick={setMissing}>
              Missing
            </Button>
            <Button small onClick={setAll}>
              All
            </Button>
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
              data={data}
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
        {upstreamUnavailableSpans.length > 0 && (
          <Box margin={{top: 16}}>
            <Alert
              intent="warning"
              title="Upstream Data Missing"
              description={
                <>
                  {upstreamUnavailableSpans.map((span) => stringForSpan(span, selected)).join(', ')}
                  {
                    ' cannot be materialized because upstream materializations are missing. Consider materializing upstream assets or '
                  }
                  <a onClick={onRemoveUpstreamUnavailable}>remove these partitions</a>
                  {` to avoid failures.`}
                </>
              }
            />
          </Box>
        )}
      </DialogBody>
      <DialogFooter
        left={partitionSet && <RunningBackfillsNotice partitionSetName={partitionSet.name} />}
      >
        <Button intent="none" onClick={() => setOpen(false)}>
          Cancel
        </Button>
        <Button intent="primary" onClick={onLaunch}>
          {launching
            ? 'Launching...'
            : selected.length !== 1
            ? `Launch ${selected.length}-Run Backfill`
            : `Launch 1 Run`}
        </Button>
      </DialogFooter>
    </>
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
      ...PythonErrorFragment
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

  ${PYTHON_ERROR_FRAGMENT}
`;
