import {useApolloClient} from '@apollo/client';
import {
  Dialog,
  DialogHeader,
  DialogBody,
  Box,
  Button,
  ButtonLink,
  DialogFooter,
  Tooltip,
  Colors,
  Alert,
} from '@dagster-io/ui';
import reject from 'lodash/reject';
import React from 'react';
import {useHistory} from 'react-router-dom';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {usePermissionsForLocation} from '../app/Permissions';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {displayNameForAssetKey, isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {PartitionHealthSummary} from '../assets/PartitionHealthSummary';
import {AssetKey} from '../assets/types';
import {
  ConfigPartitionSelectionQueryQuery,
  ConfigPartitionSelectionQueryQueryVariables,
  LaunchBackfillParams,
  LaunchPartitionBackfillMutation,
  LaunchPartitionBackfillMutationVariables,
  PartitionDefinitionForLaunchAssetFragment,
} from '../graphql/graphql';
import {LAUNCH_PARTITION_BACKFILL_MUTATION} from '../instance/BackfillUtils';
import {CONFIG_PARTITION_SELECTION_QUERY} from '../launchpad/ConfigEditorConfigPicker';
import {useLaunchPadHooks} from '../launchpad/LaunchpadHooksContext';
import {PartitionRangeWizard} from '../partitions/PartitionRangeWizard';
import {PartitionStateCheckboxes} from '../partitions/PartitionStateCheckboxes';
import {PartitionState} from '../partitions/PartitionStatus';
import {showBackfillErrorToast, showBackfillSuccessToast} from '../partitions/PartitionsBackfill';
import {assembleIntoSpans, stringForSpan} from '../partitions/SpanRepresentation';
import {RepoAddress} from '../workspace/types';

import {executionParamsForAssetJob} from './LaunchAssetExecutionButton';
import {explodePartitionKeysInRanges, mergedAssetHealth} from './MultipartitioningSupport';
import {RunningBackfillsNotice} from './RunningBackfillsNotice';
import {usePartitionDimensionRanges} from './usePartitionDimensionRanges';
import {PartitionHealthDimensionRange, usePartitionHealthData} from './usePartitionHealthData';
import {usePartitionNameForPipeline} from './usePartitionNameForPipeline';
interface Props {
  open: boolean;
  setOpen: (open: boolean) => void;
  repoAddress: RepoAddress;
  assetJobName: string;
  assets: {
    assetKey: AssetKey;
    opNames: string[];
    partitionDefinition: PartitionDefinitionForLaunchAssetFragment | null;
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

  const {canLaunchPartitionBackfill} = usePermissionsForLocation(repoAddress.location);
  const [launching, setLaunching] = React.useState(false);
  const [previewCount, setPreviewCount] = React.useState(0);
  const morePreviewsCount = partitionedAssets.length - previewCount;

  const assetHealth = usePartitionHealthData(partitionedAssets.map((a) => a.assetKey));
  const mergedHealth = React.useMemo(() => mergedAssetHealth(assetHealth), [assetHealth]);

  const knownDimensions = partitionedAssets[0].partitionDefinition?.dimensionTypes || [];
  const [ranges, setRanges] = usePartitionDimensionRanges({
    knownDimensionNames: knownDimensions.map((d) => d.name),
    modifyQueryString: false,
    assetHealth: mergedHealth,
  });

  const [stateFilters, setStateFilters] = React.useState<PartitionState[]>([
    PartitionState.MISSING,
  ]);

  const allInRanges = React.useMemo(
    () =>
      explodePartitionKeysInRanges(ranges, (dimensionKeys: string[]) => {
        // Note: If the merged asset health for a given partition is "partial", we want
        // to group it into "missing" within the backfill UI. We don't have a fine-grained
        // way to run just the missing assets within the partition.
        //
        // The alternative would be to offer a "Partial" checkbox alongside "Missing",
        // but defining missing as "missing for /any/ asset I've selected" is simpler.
        //
        const state = mergedHealth.stateForKey(dimensionKeys);
        return state === PartitionState.SUCCESS_MISSING ? PartitionState.MISSING : state;
      }),
    [ranges, mergedHealth],
  );

  const allSelected = React.useMemo(
    () => allInRanges.filter((key) => stateFilters.includes(key.state)),
    [allInRanges, stateFilters],
  );

  const client = useApolloClient();
  const history = useHistory();
  const {useLaunchWithTelemetry} = useLaunchPadHooks();
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

    if (allSelected.length === 1) {
      const {data: tagAndConfigData} = await client.query<
        ConfigPartitionSelectionQueryQuery,
        ConfigPartitionSelectionQueryQueryVariables
      >({
        query: CONFIG_PARTITION_SELECTION_QUERY,
        fetchPolicy: 'network-only',
        variables: {
          repositorySelector: {
            repositoryLocationName: repoAddress.location,
            repositoryName: repoAddress.name,
          },
          partitionSetName: partitionSet.name,
          partitionName: allSelected[0].partitionKey,
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
      if (result?.__typename === 'LaunchRunSuccess') {
        setOpen(false);
      }
    } else {
      const selectorUnlessGraph:
        | LaunchBackfillParams['selector']
        | undefined = !isHiddenAssetGroupJob(assetJobName)
        ? {
            partitionSetName: partitionSet.name,
            repositorySelector: {
              repositoryLocationName: repoAddress.location,
              repositoryName: repoAddress.name,
            },
          }
        : undefined;

      const {data: launchBackfillData} = await client.mutate<
        LaunchPartitionBackfillMutation,
        LaunchPartitionBackfillMutationVariables
      >({
        mutation: LAUNCH_PARTITION_BACKFILL_MUTATION,
        variables: {
          backfillParams: {
            selector: selectorUnlessGraph,
            assetSelection: assets.map((a) => ({path: a.assetKey.path})),
            partitionNames: allSelected.map((k) => k.partitionKey),
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

  return (
    <>
      <DialogBody>
        <Box flex={{direction: 'column', gap: 8}}>
          <Box>
            Select partitions to materialize. Click and drag to select a range on the timeline.
          </Box>

          {ranges.map((range, idx) => (
            <PartitionRangeWizard
              key={range.dimension.name}
              partitionKeys={range.dimension.partitionKeys}
              partitionStateForKey={(dimensionKey) =>
                mergedHealth.stateForSingleDimension(
                  idx,
                  dimensionKey,
                  ranges.length === 2 ? ranges[1 - idx].selected : undefined,
                )
              }
              selected={range.selected}
              setSelected={(selected) =>
                setRanges(
                  ranges.map((r) => (r.dimension === range.dimension ? {...r, selected} : r)),
                )
              }
            />
          ))}
          <PartitionStateCheckboxes
            partitionKeysForCounts={allInRanges}
            allowed={[PartitionState.MISSING, PartitionState.SUCCESS]}
            value={stateFilters}
            onChange={setStateFilters}
          />
        </Box>

        {previewCount > 0 && (
          <Box
            margin={{top: 16}}
            flex={{direction: 'column', gap: 8}}
            padding={{vertical: 16, horizontal: 20}}
            border={{side: 'horizontal', width: 1, color: Colors.KeylineGray}}
            background={Colors.Gray100}
            style={{
              marginLeft: -20,
              marginRight: -20,
              overflowY: 'auto',
              overflowX: 'visible',
              maxHeight: '35vh',
            }}
          >
            {partitionedAssets.slice(0, previewCount).map((a) => (
              <PartitionHealthSummary
                key={displayNameForAssetKey(a.assetKey)}
                assetKey={a.assetKey}
                showAssetKey
                data={assetHealth}
                ranges={ranges}
              />
            ))}
            {morePreviewsCount > 0 && (
              <Box margin={{vertical: 8}}>
                <ButtonLink onClick={() => setPreviewCount(partitionedAssets.length)}>
                  Show {morePreviewsCount} more {morePreviewsCount > 1 ? 'previews' : 'preview'}
                </ButtonLink>
              </Box>
            )}
          </Box>
        )}

        {previewCount === 0 && partitionedAssets.length > 1 && (
          <Box margin={{top: 16, bottom: 8}}>
            <ButtonLink onClick={() => setPreviewCount(5)}>
              Show per-asset partition health
            </ButtonLink>
          </Box>
        )}

        <UpstreamUnavailableWarning
          upstreamAssetKeys={upstreamAssetKeys}
          ranges={ranges}
          setRanges={setRanges}
        />
      </DialogBody>
      <DialogFooter
        left={partitionSet && <RunningBackfillsNotice partitionSetName={partitionSet.name} />}
      >
        <Button intent="none" onClick={() => setOpen(false)}>
          Cancel
        </Button>
        {allSelected.length !== 1 && !canLaunchPartitionBackfill.enabled ? (
          <Tooltip content={canLaunchPartitionBackfill.disabledReason}>
            <Button disabled>{`Launch ${allSelected.length}-Run Backfill`}</Button>
          </Tooltip>
        ) : (
          <Button
            intent="primary"
            onClick={onLaunch}
            disabled={allSelected.length === 0}
            loading={launching}
          >
            {launching
              ? 'Launching...'
              : allSelected.length !== 1
              ? `Launch ${allSelected.length}-Run Backfill`
              : `Launch 1 Run`}
          </Button>
        )}
      </DialogFooter>
    </>
  );
};

const UpstreamUnavailableWarning: React.FC<{
  upstreamAssetKeys: AssetKey[];
  ranges: PartitionHealthDimensionRange[];
  setRanges: (next: PartitionHealthDimensionRange[]) => void;
}> = ({upstreamAssetKeys, ranges, setRanges}) => {
  // We want to warn if an immediately upstream asset 1) has the same partitioning and
  // 2) is missing materializations for keys in `allSelected`. We only offer this feature
  // for single-dimensional partitioned assets because it's difficult to express the
  // unavailable partitions in the multi-dimensional case and our "two range inputs" won't
  // allow us to remove missing individual pairs.
  const upstreamAssetHealth = usePartitionHealthData(upstreamAssetKeys);
  if (upstreamAssetHealth.length === 0) {
    return <span />;
  }

  const upstreamUnavailable = (singleDimensionKey: string) =>
    upstreamAssetHealth.some((a) => {
      // If the key is not undefined, it's present in the partition key space of the asset
      return a.stateForKey([singleDimensionKey]) === PartitionState.MISSING;
    });

  const upstreamUnavailableSpans =
    ranges.length === 1
      ? assembleIntoSpans(ranges[0].selected, upstreamUnavailable).filter((s) => s.status === true)
      : [];

  const onRemoveUpstreamUnavailable = () => {
    if (ranges.length > 1) {
      throw new Error('Assertion failed, this feature is only available for 1 dimensional assets');
    }
    setRanges([{...ranges[0], selected: reject(ranges[0].selected, upstreamUnavailable)}]);
  };

  if (upstreamUnavailableSpans.length === 0) {
    return <span />;
  }

  return (
    <Box margin={{top: 16}}>
      <Alert
        intent="warning"
        title="Upstream data missing"
        description={
          <>
            {upstreamUnavailableSpans
              .map((span) => stringForSpan(span, ranges[0].selected))
              .join(', ')}
            {
              ' cannot be materialized because upstream materializations are missing. Consider materializing upstream assets or '
            }
            <ButtonLink underline="always" onClick={onRemoveUpstreamUnavailable}>
              remove these partitions
            </ButtonLink>
            {` to avoid failures.`}
          </>
        }
      />
    </Box>
  );
};
