import {gql, useApolloClient, useQuery} from '@apollo/client';
import {
  Box,
  Button,
  ButtonLink,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  DialogHeader,
  Tooltip,
  Alert,
  Checkbox,
  Icon,
  Subheading,
} from '@dagster-io/ui';
import reject from 'lodash/reject';
import React from 'react';
import {useHistory} from 'react-router-dom';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PipelineRunTag} from '../app/ExecutionSessionStorage';
import {usePermissionsForLocation} from '../app/Permissions';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {displayNameForAssetKey, itemWithAssetKey} from '../asset-graph/Utils';
import {AssetKey} from '../assets/types';
import {LaunchBackfillParams, PartitionDefinitionType} from '../graphql/types';
import {useStateWithUpdateCallback} from '../hooks/useStateWithUpdateCallback';
import {LAUNCH_PARTITION_BACKFILL_MUTATION} from '../instance/BackfillUtils';
import {
  LaunchPartitionBackfillMutation,
  LaunchPartitionBackfillMutationVariables,
} from '../instance/types/BackfillUtils.types';
import {CONFIG_PARTITION_SELECTION_QUERY} from '../launchpad/ConfigEditorConfigPicker';
import {useLaunchPadHooks} from '../launchpad/LaunchpadHooksContext';
import {TagEditor, TagContainer} from '../launchpad/TagEditor';
import {
  ConfigPartitionSelectionQuery,
  ConfigPartitionSelectionQueryVariables,
} from '../launchpad/types/ConfigEditorConfigPicker.types';
import {
  DaemonNotRunningAlert,
  DAEMON_NOT_RUNNING_ALERT_INSTANCE_FRAGMENT,
  showBackfillErrorToast,
  showBackfillSuccessToast,
  UsingDefaultLauncherAlert,
  USING_DEFAULT_LAUNCH_ERALERT_INSTANCE_FRAGMENT,
} from '../partitions/BackfillMessaging';
import {Section} from '../partitions/BackfillSelector';
import {DimensionRangeWizard} from '../partitions/DimensionRangeWizard';
import {PartitionState} from '../partitions/PartitionStatus';
import {assembleIntoSpans, stringForSpan} from '../partitions/SpanRepresentation';
import {DagsterTag} from '../runs/RunTag';
import {testId} from '../testing/testId';
import {RepoAddress} from '../workspace/types';

import {
  executionParamsForAssetJob,
  LaunchAssetsChoosePartitionsTarget,
} from './LaunchAssetExecutionButton';
import {
  explodePartitionKeysInSelection,
  mergedAssetHealth,
  partitionDefinitionsEqual,
} from './MultipartitioningSupport';
import {PartitionHealthSummary} from './PartitionHealthSummary';
import {RunningBackfillsNotice} from './RunningBackfillsNotice';
import {
  LaunchAssetChoosePartitionsQuery,
  LaunchAssetChoosePartitionsQueryVariables,
} from './types/LaunchAssetChoosePartitionsDialog.types';
import {PartitionDefinitionForLaunchAssetFragment} from './types/LaunchAssetExecutionButton.types';
import {usePartitionDimensionSelections} from './usePartitionDimensionSelections';
import {PartitionDimensionSelection, usePartitionHealthData} from './usePartitionHealthData';

interface Props {
  open: boolean;
  setOpen: (open: boolean) => void;
  repoAddress: RepoAddress;
  target: LaunchAssetsChoosePartitionsTarget;
  assets: {
    assetKey: AssetKey;
    opNames: string[];
    partitionDefinition: PartitionDefinitionForLaunchAssetFragment | null;
  }[];
  upstreamAssetKeys: AssetKey[]; // single layer of upstream dependencies
  refetch?: () => Promise<void>;
}

export const LaunchAssetChoosePartitionsDialog: React.FC<Props> = (props) => {
  const displayName =
    props.assets.length > 1
      ? `${props.assets.length} assets`
      : displayNameForAssetKey(props.assets[0].assetKey);

  const title = `Launch runs to materialize ${displayName}`;

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
  target,
  upstreamAssetKeys,
  refetch: _refetch,
}) => {
  const partitionedAssets = assets.filter((a) => !!a.partitionDefinition);

  const {canLaunchPipelineExecution, canLaunchPartitionBackfill} = usePermissionsForLocation(
    repoAddress.location,
  );
  const [launching, setLaunching] = React.useState(false);
  const [tagEditorOpen, setTagEditorOpen] = React.useState<boolean>(false);
  const [tags, setTags] = React.useState<PipelineRunTag[]>([]);

  const [previewCount, setPreviewCount] = React.useState(0);
  const morePreviewsCount = partitionedAssets.length - previewCount;

  const [lastRefresh, setLastRefresh] = React.useState(Date.now());

  const refetch = async () => {
    await _refetch?.();
    setLastRefresh(Date.now());
  };

  const assetHealth = usePartitionHealthData(
    partitionedAssets.map((a) => a.assetKey),
    lastRefresh.toString(),
    'immediate',
  );

  const assetHealthLoading = assetHealth.length === 0;

  const displayedHealth = React.useMemo(() => {
    if (target.type === 'job' || assetHealthLoading) {
      return mergedAssetHealth(assetHealth);
    }
    return assetHealth.find(itemWithAssetKey(target.anchorAssetKey)) || mergedAssetHealth([]);
  }, [assetHealth, assetHealthLoading, target]);

  const displayedPartitionDefinition =
    target.type === 'job'
      ? partitionedAssets[0].partitionDefinition
      : partitionedAssets.find(itemWithAssetKey(target.anchorAssetKey))?.partitionDefinition;

  const knownDimensions = partitionedAssets[0].partitionDefinition?.dimensionTypes || [];
  const [missingFailedOnly, setMissingFailedOnly] = React.useState(true);

  const [selections, _setSelections] = usePartitionDimensionSelections({
    knownDimensionNames: knownDimensions.map((d) => d.name),
    modifyQueryString: false,
    assetHealth: displayedHealth,
    skipPartitionKeyValidation:
      displayedPartitionDefinition?.type === PartitionDefinitionType.DYNAMIC,
  });

  const [_, setSelections] = useStateWithUpdateCallback(selections, _setSelections);

  const keysInSelection = React.useMemo(
    () =>
      explodePartitionKeysInSelection(selections, (dimensionKeys: string[]) => {
        // Note: If the merged asset health for a given partition is "partial", we want
        // to group it into "missing" within the backfill UI. We don't have a fine-grained
        // way to run just the missing assets within the partition.
        //
        // The alternative would be to offer a "Partial" checkbox alongside "Missing",
        // but defining missing as "missing for /any/ asset I've selected" is simpler.
        //
        const state = displayedHealth.stateForKey(dimensionKeys);
        return state === PartitionState.SUCCESS_MISSING ? PartitionState.MISSING : state;
      }),
    [selections, displayedHealth],
  );

  const [launchWithRangesAsTags, setLaunchWithRangesAsTags] = React.useState(false);
  const canLaunchWithRangesAsTags =
    selections.every((s) => s.selectedRanges.length === 1) &&
    selections.some((s) => s.selectedKeys.length > 1);

  const keysFiltered = React.useMemo(
    () =>
      missingFailedOnly
        ? keysInSelection.filter((key) =>
            [PartitionState.MISSING, PartitionState.FAILURE].includes(key.state),
          )
        : keysInSelection,
    [keysInSelection, missingFailedOnly],
  );

  const client = useApolloClient();
  const history = useHistory();
  const instanceResult = useQuery<
    LaunchAssetChoosePartitionsQuery,
    LaunchAssetChoosePartitionsQueryVariables
  >(LAUNCH_ASSET_CHOOSE_PARTITIONS_QUERY);
  const instance = instanceResult.data?.instance;

  const {useLaunchWithTelemetry} = useLaunchPadHooks();
  const launchWithTelemetry = useLaunchWithTelemetry();
  const launchAsBackfill =
    target.type === 'pureAssetBackfill' || (!launchWithRangesAsTags && keysFiltered.length !== 1);

  React.useEffect(() => {
    !canLaunchWithRangesAsTags && setLaunchWithRangesAsTags(false);
  }, [canLaunchWithRangesAsTags]);

  React.useEffect(() => {
    launchWithRangesAsTags && setMissingFailedOnly(false);
  }, [launchWithRangesAsTags]);

  React.useEffect(() => {
    target.type === 'pureAssetBackfill' && setMissingFailedOnly(false);
  }, [target]);

  const onLaunch = async () => {
    setLaunching(true);

    if (launchAsBackfill) {
      await onLaunchAsBackfill();
    } else {
      await onLaunchAsSingleRun();
    }
    setLaunching(false);
  };

  const onLaunchAsSingleRun = async () => {
    if (!('jobName' in target)) {
      // Should never happen, this is essentially an assertion failure
      showCustomAlert({
        title: 'Unable to launch as single run',
        body:
          'This selection is not valid for a single run launch. ' +
          'Please report this error to the Dagster team.',
      });
      return;
    }

    if (!canLaunchPipelineExecution.enabled) {
      // Should never happen, this is essentially an assertion failure
      showCustomAlert({
        title: 'Unable to launch as single run',
        body: 'You do not have permission to launch this job.',
      });
    }

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
        partitionSetName: target.partitionSetName,
        partitionName: keysFiltered[0].partitionKey,
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
      showCustomAlert({
        title: 'Unable to load tags',
        body: <PythonErrorInfo error={partition.tagsOrError} />,
      });
      return;
    }
    if (partition.runConfigOrError.__typename === 'PythonError') {
      showCustomAlert({
        title: 'Unable to load tags',
        body: <PythonErrorInfo error={partition.runConfigOrError} />,
      });
      return;
    }

    const runConfigData = partition.runConfigOrError.yaml || '';
    let allTags = [...partition.tagsOrError.results, ...tags];

    if (launchWithRangesAsTags) {
      allTags = allTags.filter((t) => !t.key.startsWith(DagsterTag.Partition));
      allTags.push({
        key: DagsterTag.AssetPartitionRangeStart,
        value: keysInSelection[0].partitionKey,
      });
      allTags.push({
        key: DagsterTag.AssetPartitionRangeEnd,
        value: keysInSelection[keysInSelection.length - 1].partitionKey,
      });
    }

    const result = await launchWithTelemetry(
      {
        executionParams: {
          ...executionParamsForAssetJob(repoAddress, target.jobName, assets, allTags),
          runConfigData,
          mode: partition.mode,
        },
      },
      'toast',
    );

    if (result?.__typename === 'LaunchRunSuccess') {
      setOpen(false);
    }
  };

  const onLaunchAsBackfill = async () => {
    const selectorIfJobPage: LaunchBackfillParams['selector'] | undefined =
      'jobName' in target
        ? {
            partitionSetName: target.partitionSetName,
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
          selector: selectorIfJobPage,
          assetSelection: assets.map((a) => ({path: a.assetKey.path})),
          partitionNames: keysFiltered.map((k) => k.partitionKey),
          fromFailure: false,
          tags,
        },
      },
    });

    if (launchBackfillData?.launchPartitionBackfill.__typename === 'LaunchBackfillSuccess') {
      showBackfillSuccessToast(history, launchBackfillData?.launchPartitionBackfill.backfillId);
      setOpen(false);
    } else {
      showBackfillErrorToast(launchBackfillData);
    }
  };

  const launchButton = () => {
    if (launchAsBackfill && !canLaunchPartitionBackfill.enabled) {
      return (
        <Tooltip content={canLaunchPartitionBackfill.disabledReason}>
          <Button disabled>
            {target.type === 'job'
              ? `Launch ${keysFiltered.length}-run backfill`
              : 'Launch backfill'}
          </Button>
        </Tooltip>
      );
    }

    if (!launchAsBackfill && !canLaunchPipelineExecution.enabled) {
      return (
        <Tooltip content={canLaunchPipelineExecution.disabledReason}>
          <Button disabled>Launch 1 run</Button>
        </Tooltip>
      );
    }

    return (
      <Button
        data-testid={testId('launch-button')}
        intent="primary"
        onClick={onLaunch}
        disabled={keysFiltered.length === 0}
        loading={launching}
      >
        {launching
          ? 'Launching...'
          : launchAsBackfill
          ? target.type === 'job'
            ? `Launch ${keysFiltered.length}-run backfill`
            : 'Launch backfill'
          : `Launch 1 run`}
      </Button>
    );
  };

  return (
    <>
      <DialogBody data-testid={testId('choose-partitions-dialog')}>
        <Box flex={{direction: 'column', gap: 8}}>
          {target.type === 'pureAssetBackfill' && (
            <Box flex={{gap: 8}} data-testid={testId('anchor-asset-label')}>
              <Icon name="asset" size={20} />
              <Subheading>{displayNameForAssetKey(target.anchorAssetKey)}</Subheading>
            </Box>
          )}

          <Box>
            Select partitions to materialize.{' '}
            {displayedPartitionDefinition?.type === PartitionDefinitionType.TIME_WINDOW
              ? 'Click and drag to select a range on the timeline.'
              : null}
          </Box>

          {selections.map((range, idx) => (
            <DimensionRangeWizard
              key={range.dimension.name}
              partitionKeys={range.dimension.partitionKeys}
              health={{
                ranges: displayedHealth.rangesForSingleDimension(
                  idx,
                  selections.length === 2 ? selections[1 - idx].selectedRanges : undefined,
                ),
              }}
              isDynamic={displayedPartitionDefinition?.type === PartitionDefinitionType.DYNAMIC}
              selected={range.selectedKeys}
              setSelected={(selectedKeys) =>
                setSelections((selections) =>
                  selections.map((r) =>
                    r.dimension === range.dimension ? {...r, selectedKeys} : r,
                  ),
                )
              }
              partitionDefinitionName={displayedPartitionDefinition?.name}
              repoAddress={repoAddress}
              refetch={refetch}
            />
          ))}

          {target.type === 'pureAssetBackfill' ? (
            <Alert
              intent="info"
              title="Dagster will materialize all partitions downstream of the selected partitions for the selected assets, using separate runs as needed."
            />
          ) : (
            <Box flex={{justifyContent: 'space-between'}}>
              <Checkbox
                data-testid={testId('missing-only-checkbox')}
                label="Missing and failed partitions only"
                checked={missingFailedOnly}
                disabled={launchWithRangesAsTags}
                onChange={() => setMissingFailedOnly(!missingFailedOnly)}
              />

              <Checkbox
                data-testid={testId('ranges-as-tags-checkbox')}
                label={
                  <Box flex={{alignItems: 'center', gap: 4}}>
                    Pass partition ranges to single run
                    <Tooltip
                      position="top-left"
                      content={
                        <div style={{maxWidth: 300}}>
                          This option requires that your assets are written to operate on a
                          partition key range via context.asset_partition_key_range_for_output or
                          context.asset_partitions_time_window_for_output.
                        </div>
                      }
                    >
                      <Icon name="info" color={Colors.Gray500} />
                    </Tooltip>
                  </Box>
                }
                checked={launchWithRangesAsTags}
                disabled={!canLaunchWithRangesAsTags}
                onChange={() => setLaunchWithRangesAsTags(!launchWithRangesAsTags)}
              />
            </Box>
          )}
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
                selections={
                  a.partitionDefinition &&
                  displayedPartitionDefinition &&
                  partitionDefinitionsEqual(a.partitionDefinition, displayedPartitionDefinition)
                    ? selections
                    : undefined
                }
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
          selections={selections}
          setSelections={setSelections}
        />

        <Box flex={{direction: 'column', gap: 16}} style={{marginTop: 24}}>
          <Section title="Tags">
            <TagEditor
              tagsFromSession={tags}
              onChange={setTags}
              open={tagEditorOpen}
              onRequestClose={() => setTagEditorOpen(false)}
            />
            {tags.length ? (
              <div style={{border: `1px solid ${Colors.Gray300}`, borderRadius: 8, padding: 3}}>
                <TagContainer tagsFromSession={tags} onRequestEdit={() => setTagEditorOpen(true)} />
              </div>
            ) : (
              <div>
                <Button onClick={() => setTagEditorOpen(true)}>
                  {launchAsBackfill ? 'Add tags to backfill runs' : 'Add tags'}
                </Button>
              </div>
            )}
          </Section>

          {instance && launchAsBackfill && <DaemonNotRunningAlert instance={instance} />}

          {instance && launchAsBackfill && <UsingDefaultLauncherAlert instance={instance} />}
        </Box>
      </DialogBody>

      <DialogFooter
        left={
          'partitionSetName' in target && (
            <RunningBackfillsNotice partitionSetName={target.partitionSetName} />
          )
        }
      >
        <Button intent="none" onClick={() => setOpen(false)}>
          Cancel
        </Button>
        {launchButton()}
      </DialogFooter>
    </>
  );
};

const UpstreamUnavailableWarning: React.FC<{
  upstreamAssetKeys: AssetKey[];
  selections: PartitionDimensionSelection[];
  setSelections: (next: PartitionDimensionSelection[]) => void;
}> = ({upstreamAssetKeys, selections, setSelections}) => {
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
    selections.length === 1
      ? assembleIntoSpans(selections[0].selectedKeys, upstreamUnavailable).filter(
          (s) => s.status === true,
        )
      : [];

  const onRemoveUpstreamUnavailable = () => {
    if (selections.length > 1) {
      throw new Error('Assertion failed, this feature is only available for 1 dimensional assets');
    }
    setSelections([
      {...selections[0], selectedKeys: reject(selections[0].selectedKeys, upstreamUnavailable)},
    ]);
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
              .map((span) => stringForSpan(span, selections[0].selectedKeys))
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

export const LAUNCH_ASSET_CHOOSE_PARTITIONS_QUERY = gql`
  query LaunchAssetChoosePartitionsQuery {
    instance {
      ...DaemonNotRunningAlertInstanceFragment
      ...UsingDefaultLauncherAlertInstanceFragment
    }
  }

  ${DAEMON_NOT_RUNNING_ALERT_INSTANCE_FRAGMENT}
  ${USING_DEFAULT_LAUNCH_ERALERT_INSTANCE_FRAGMENT}
`;
