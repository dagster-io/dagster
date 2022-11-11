import {useApolloClient} from '@apollo/client';
import {
  Dialog,
  DialogHeader,
  DialogBody,
  Box,
  Button,
  ButtonLink,
  DialogFooter,
  Alert,
  Tooltip,
  Colors,
} from '@dagster-io/ui';
import reject from 'lodash/reject';
import React from 'react';
import {useHistory} from 'react-router-dom';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {usePermissions} from '../app/Permissions';
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
import {assembleIntoSpans, stringForSpan} from '../partitions/PartitionRangeInput';
import {PartitionRangeWizard, PartitionStateCheckboxes} from '../partitions/PartitionRangeWizard';
import {PartitionState} from '../partitions/PartitionStatus';
import {showBackfillErrorToast, showBackfillSuccessToast} from '../partitions/PartitionsBackfill';
import {RepoAddress} from '../workspace/types';

import {executionParamsForAssetJob} from './LaunchAssetExecutionButton';
import {RunningBackfillsNotice} from './RunningBackfillsNotice';
import {LaunchAssetExecutionAssetNodeFragment_partitionDefinition} from './types/LaunchAssetExecutionAssetNodeFragment';
import {usePartitionNameForPipeline} from './usePartitionNameForPipeline';

interface Props {
  open: boolean;
  setOpen: (open: boolean) => void;
  repoAddress: RepoAddress;
  assetJobName: string;
  assets: {
    assetKey: AssetKey;
    opNames: string[];
    partitionDefinition: LaunchAssetExecutionAssetNodeFragment_partitionDefinition | null;
  }[];
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
  const partitionedAssets = assets.filter((a) => !!a.partitionDefinition);
  const assetHealth = usePartitionHealthData(partitionedAssets.map((a) => a.assetKey));
  const upstreamAssetHealth = usePartitionHealthData(upstreamAssetKeys);

  const partitionStatusData = React.useMemo(() => assetHealthToPartitionStatus(assetHealth), [
    assetHealth,
  ]);
  const partitionKeys = React.useMemo(() => (assetHealth[0] ? assetHealth[0].keys : []), [
    assetHealth,
  ]);

  const {canLaunchPartitionBackfill} = usePermissions();

  const mostRecentKey = partitionKeys[partitionKeys.length - 1];

  const [range, setRange] = React.useState<string[]>([]);
  const [stateFilters, setStateFilters] = React.useState<PartitionState[]>([
    PartitionState.MISSING,
    PartitionState.FAILURE,
    PartitionState.SUCCESS,
  ]);

  const [previewCount, setPreviewCount] = React.useState(0);
  const [launching, setLaunching] = React.useState(false);

  React.useEffect(() => {
    setRange([mostRecentKey]);
  }, [mostRecentKey]);

  const selected = React.useMemo(() => {
    return range.filter((r) => stateFilters.includes(partitionStatusData[r]));
  }, [range, stateFilters, partitionStatusData]);

  const client = useApolloClient();
  const history = useHistory();
  const launchWithTelemetry = useLaunchWithTelemetry();

  // Find the partition set name. This seems like a bit of a hack, unclear
  // how it would work if there were two different partition spaces in the asset job
  const {partitionSet, partitionSetError} = usePartitionNameForPipeline(repoAddress, assetJobName);

  const onLaunch = async () => {
    setLaunching(true);

    if (!partitionSet) {
      setLaunching(false);
      showCustomAlert({
        title: `Unable to find partition set on ${assetJobName}`,
        body: partitionSetError ? <PythonErrorInfo error={partitionSetError} /> : <span />,
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
            assetSelection: assets.map((a) => ({path: a.assetKey.path})),
            partitionNames: selected,
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
    upstreamAssetHealth.length > 0 &&
    upstreamAssetHealth.some((a) => a.keys.includes(key) && !a.statusByPartition[key]);

  const upstreamUnavailableSpans = assembleIntoSpans(selected, upstreamUnavailable).filter(
    (s) => s.status === true,
  );
  const onRemoveUpstreamUnavailable = () => {
    setRange(reject(selected, upstreamUnavailable));
  };

  return (
    <>
      <DialogBody>
        <Box flex={{direction: 'column', gap: 8}}>
          <Box>Select the set of partitions to materialze. View the selection syntax guide</Box>

          <PartitionRangeWizard
            all={partitionKeys}
            selected={range}
            setSelected={setRange}
            partitionData={partitionStatusData}
          />
          <PartitionStateCheckboxes
            partitionData={partitionStatusData}
            partitionKeysForCounts={range}
            value={stateFilters}
            onChange={setStateFilters}
          />
        </Box>
        <Box
          flex={{direction: 'column', gap: 8}}
          border={{side: 'top', width: 1, color: Colors.KeylineGray}}
          style={{marginTop: 16, overflowY: 'auto', overflowX: 'visible', maxHeight: '50vh'}}
        >
          {partitionedAssets.slice(0, previewCount).map((a) => (
            <PartitionHealthSummary
              assetKey={a.assetKey}
              showAssetKey
              key={displayNameForAssetKey(a.assetKey)}
              data={assetHealth}
              selected={selected}
            />
          ))}
          {previewCount === 0 ? (
            <Box margin={{vertical: 8}}>
              <ButtonLink onClick={() => setPreviewCount(5)}>
                Show per-asset partition health
              </ButtonLink>
            </Box>
          ) : previewCount < partitionedAssets.length ? (
            <Box margin={{vertical: 8}}>
              <ButtonLink onClick={() => setPreviewCount(partitionedAssets.length)}>
                Show {partitionedAssets.length - previewCount} more previews
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
        {selected.length !== 1 && !canLaunchPartitionBackfill.enabled ? (
          <Tooltip content={canLaunchPartitionBackfill.disabledReason}>
            <Button disabled>{`Launch ${selected.length}-Run Backfill`}</Button>
          </Tooltip>
        ) : (
          <Button
            intent="primary"
            onClick={onLaunch}
            disabled={selected.length === 0}
            loading={launching}
          >
            {launching
              ? 'Launching...'
              : selected.length !== 1
              ? `Launch ${selected.length}-Run Backfill`
              : `Launch 1 Run`}
          </Button>
        )}
      </DialogFooter>
    </>
  );
};
