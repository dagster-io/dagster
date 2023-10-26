import {gql, useApolloClient, useQuery} from '@apollo/client';
// eslint-disable-next-line no-restricted-imports
import {Radio} from '@blueprintjs/core';
import {
  Box,
  Button,
  ButtonLink,
  Colors,
  Dialog,
  DialogFooter,
  DialogHeader,
  Tooltip,
  Alert,
  Checkbox,
  Icon,
  Subheading,
  RadioContainer,
} from '@dagster-io/ui-components';
import reject from 'lodash/reject';
import React from 'react';
import {useHistory} from 'react-router-dom';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PipelineRunTag} from '../app/ExecutionSessionStorage';
import {usePermissionsForLocation} from '../app/Permissions';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {
  displayNameForAssetKey,
  isHiddenAssetGroupJob,
  itemWithAssetKey,
} from '../asset-graph/Utils';
import {AssetKey} from '../assets/types';
import {AssetCheck, LaunchBackfillParams, PartitionDefinitionType} from '../graphql/types';
import {LAUNCH_PARTITION_BACKFILL_MUTATION} from '../instance/backfill/BackfillUtils';
import {
  LaunchPartitionBackfillMutation,
  LaunchPartitionBackfillMutationVariables,
} from '../instance/backfill/types/BackfillUtils.types';
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
  USING_DEFAULT_LAUNCHER_ALERT_INSTANCE_FRAGMENT,
} from '../partitions/BackfillMessaging';
import {DimensionRangeWizard} from '../partitions/DimensionRangeWizard';
import {assembleIntoSpans, stringForSpan} from '../partitions/SpanRepresentation';
import {DagsterTag} from '../runs/RunTag';
import {testId} from '../testing/testId';
import {ToggleableSection} from '../ui/ToggleableSection';
import {useFeatureFlagForCodeLocation} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

import {partitionCountString} from './AssetNodePartitionCounts';
import {AssetPartitionStatus} from './AssetPartitionStatus';
import {
  executionParamsForAssetJob,
  LaunchAssetsChoosePartitionsTarget,
} from './LaunchAssetExecutionButton';
import {
  explodePartitionKeysInSelectionMatching,
  mergedAssetHealth,
  partitionDefinitionsEqual,
} from './MultipartitioningSupport';
import {PartitionHealthSummary} from './PartitionHealthSummary';
import {RunningBackfillsNotice} from './RunningBackfillsNotice';
import {asAssetKeyInput} from './asInput';
import {
  LaunchAssetWarningsQuery,
  LaunchAssetWarningsQueryVariables,
} from './types/LaunchAssetChoosePartitionsDialog.types';
import {PartitionDefinitionForLaunchAssetFragment} from './types/LaunchAssetExecutionButton.types';
import {usePartitionDimensionSelections} from './usePartitionDimensionSelections';
import {
  keyCountInSelections,
  PartitionDimensionSelection,
  usePartitionHealthData,
} from './usePartitionHealthData';

const MISSING_FAILED_STATUSES = [AssetPartitionStatus.MISSING, AssetPartitionStatus.FAILED];

interface Props {
  open: boolean;
  setOpen: (open: boolean) => void;
  repoAddress: RepoAddress;
  target: LaunchAssetsChoosePartitionsTarget;
  assets: {
    assetKey: AssetKey;
    assetChecks: Pick<AssetCheck, 'name'>[];
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
      : displayNameForAssetKey(props.assets[0]!.assetKey);

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

  const {
    permissions: {canLaunchPipelineExecution, canLaunchPartitionBackfill},
    disabledReasons,
  } = usePermissionsForLocation(repoAddress.location);
  const [launching, setLaunching] = React.useState(false);
  const [tagEditorOpen, setTagEditorOpen] = React.useState<boolean>(false);
  const [tags, setTags] = React.useState<PipelineRunTag[]>([]);

  const [previewCount, setPreviewCount] = React.useState(0);
  const morePreviewsCount = partitionedAssets.length - previewCount;

  const showSingleRunBackfillToggle = useFeatureFlagForCodeLocation(
    repoAddress.location,
    'SHOW_SINGLE_RUN_BACKFILL_TOGGLE',
  );

  const [lastRefresh, setLastRefresh] = React.useState(Date.now());

  const refetch = async () => {
    await _refetch?.();
    setLastRefresh(Date.now());
  };

  const assetHealth = usePartitionHealthData(
    partitionedAssets.map((a) => a.assetKey),
    lastRefresh.toString(),
    'background',
  );

  const assetHealthLoading = assetHealth.length === 0;

  const displayedHealth = React.useMemo(() => {
    if (target.type === 'pureAll') {
      return mergedAssetHealth([]);
    }
    if (target.type === 'job' || assetHealthLoading) {
      return mergedAssetHealth(assetHealth);
    }
    return assetHealth.find(itemWithAssetKey(target.anchorAssetKey)) || mergedAssetHealth([]);
  }, [assetHealth, assetHealthLoading, target]);

  const displayedBaseAsset =
    target.type === 'job'
      ? partitionedAssets[0]
      : target.type === 'pureWithAnchorAsset'
      ? partitionedAssets.find(itemWithAssetKey(target.anchorAssetKey))
      : null;

  const displayedPartitionDefinition = displayedBaseAsset?.partitionDefinition;

  const knownDimensions = partitionedAssets[0]!.partitionDefinition?.dimensionTypes || [];
  const [missingFailedOnly, setMissingFailedOnly] = React.useState(false);

  const [selections, setSelections] = usePartitionDimensionSelections({
    knownDimensionNames: knownDimensions.map((d) => d.name),
    modifyQueryString: false,
    assetHealth: displayedHealth,
    skipPartitionKeyValidation:
      displayedPartitionDefinition?.type === PartitionDefinitionType.DYNAMIC,
    shouldReadPartitionQueryStringParam: true,
  });

  const [launchWithRangesAsTags, setLaunchWithRangesAsTags] = React.useState(false);
  const canLaunchWithRangesAsTags =
    selections.every((s) => s.selectedRanges.length === 1) &&
    selections.some((s) => s.selectedKeys.length > 1);

  const keysFiltered = React.useMemo(() => {
    return explodePartitionKeysInSelectionMatching(selections, (dIdxs) => {
      if (missingFailedOnly) {
        const state = displayedHealth.stateForKeyIdx(dIdxs);
        return state instanceof Array
          ? state.some((s) => MISSING_FAILED_STATUSES.includes(s))
          : MISSING_FAILED_STATUSES.includes(state);
      }
      return true;
    });
  }, [missingFailedOnly, selections, displayedHealth]);

  const client = useApolloClient();
  const history = useHistory();

  const {useLaunchWithTelemetry} = useLaunchPadHooks();
  const launchWithTelemetry = useLaunchWithTelemetry();
  const launchAsBackfill =
    ['pureWithAnchorAsset', 'pureAll'].includes(target.type) ||
    (!launchWithRangesAsTags && keysFiltered.length !== 1);

  React.useEffect(() => {
    !canLaunchWithRangesAsTags && setLaunchWithRangesAsTags(false);
  }, [canLaunchWithRangesAsTags]);

  React.useEffect(() => {
    launchWithRangesAsTags && setMissingFailedOnly(false);
  }, [launchWithRangesAsTags]);

  React.useEffect(() => {
    ['pureWithAnchorAsset', 'pureAll'].includes(target.type) && setMissingFailedOnly(false);
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

    if (!canLaunchPipelineExecution) {
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
        partitionName: keysFiltered[0]!,
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
        value: keysFiltered[0]!,
      });
      allTags.push({
        key: DagsterTag.AssetPartitionRangeEnd,
        value: keysFiltered[keysFiltered.length - 1]!,
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
    const backfillParams: LaunchBackfillParams =
      target.type === 'job' && !isHiddenAssetGroupJob(target.jobName)
        ? {
            tags,
            assetSelection: assets.map(asAssetKeyInput),
            partitionNames: keysFiltered,
            fromFailure: false,
            selector: {
              partitionSetName: target.partitionSetName,
              repositorySelector: {
                repositoryLocationName: repoAddress.location,
                repositoryName: repoAddress.name,
              },
            },
          }
        : target.type === 'pureAll'
        ? {
            tags,
            assetSelection: assets.map(asAssetKeyInput),
            allPartitions: true,
          }
        : {
            tags,
            assetSelection: assets.map(asAssetKeyInput),
            partitionNames: keysFiltered,
            fromFailure: false,
          };

    const {data: launchBackfillData} = await client.mutate<
      LaunchPartitionBackfillMutation,
      LaunchPartitionBackfillMutationVariables
    >({
      mutation: LAUNCH_PARTITION_BACKFILL_MUTATION,
      variables: {backfillParams},
    });

    if (launchBackfillData?.launchPartitionBackfill.__typename === 'LaunchBackfillSuccess') {
      showBackfillSuccessToast(
        history,
        launchBackfillData?.launchPartitionBackfill.backfillId,
        true,
      );
      setOpen(false);
    } else {
      showBackfillErrorToast(launchBackfillData);
    }
  };

  const launchButton = () => {
    if (launchAsBackfill && !canLaunchPartitionBackfill) {
      return (
        <Tooltip content={disabledReasons.canLaunchPartitionBackfill}>
          <Button disabled>
            {target.type === 'job'
              ? `Launch ${keysFiltered.length}-run backfill`
              : 'Launch backfill'}
          </Button>
        </Tooltip>
      );
    }

    if (!launchAsBackfill && !canLaunchPipelineExecution) {
      return (
        <Tooltip content={disabledReasons.canLaunchPipelineExecution}>
          <Button disabled>Launch 1 run</Button>
        </Tooltip>
      );
    }

    return (
      <Button
        data-testid={testId('launch-button')}
        intent="primary"
        onClick={onLaunch}
        disabled={target.type === 'pureAll' ? false : keysFiltered.length === 0}
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
      <div data-testid={testId('choose-partitions-dialog')}>
        <Warnings
          displayedPartitionDefinition={displayedPartitionDefinition}
          launchAsBackfill={launchAsBackfill}
          upstreamAssetKeys={upstreamAssetKeys}
          selections={selections}
          setSelections={setSelections}
        />
        {target.type === 'pureAll' ? (
          <ToggleableSection
            isInitiallyOpen={true}
            title={
              <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
                <Subheading>Partition selection</Subheading>
                <span>All partitions</span>
              </Box>
            }
          >
            <Box
              padding={{vertical: 12, horizontal: 20}}
              data-testid={testId('pure-all-partitions-only')}
            >
              <Alert
                key="alert"
                intent="info"
                title="The root assets of this selection have different partition definitions. To backfill a specific partition or partition range, select a subset of the assets."
              />
            </Box>
          </ToggleableSection>
        ) : (
          <ToggleableSection
            isInitiallyOpen={true}
            title={
              <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
                <Subheading>Partition selection</Subheading>
                {target.type === 'pureWithAnchorAsset' ? (
                  <span /> // we won't know until runtime
                ) : (
                  <span>{partitionCountString(keyCountInSelections(selections))}</span>
                )}
              </Box>
            }
          >
            {target.type === 'pureWithAnchorAsset' && (
              <Box
                flex={{alignItems: 'center', gap: 8}}
                padding={{top: 12, horizontal: 20}}
                data-testid={testId('anchor-asset-label')}
              >
                <Icon name="asset" />
                <Subheading>{displayNameForAssetKey(target.anchorAssetKey)}</Subheading>
              </Box>
            )}
            {selections.map((range, idx) => (
              <Box
                key={range.dimension.name}
                border="bottom"
                padding={{vertical: 12, horizontal: 20}}
              >
                <Box as={Subheading} flex={{alignItems: 'center', gap: 8}}>
                  <Icon name="partition" />
                  {range.dimension.name}
                </Box>
                <Box>
                  Select partitions to materialize.{' '}
                  {range.dimension.type === PartitionDefinitionType.TIME_WINDOW
                    ? 'Click and drag to select a range on the timeline.'
                    : null}
                </Box>
                <DimensionRangeWizard
                  partitionKeys={range.dimension.partitionKeys}
                  health={{
                    ranges: displayedHealth.rangesForSingleDimension(
                      idx,
                      selections.length === 2 ? selections[1 - idx]!.selectedRanges : undefined,
                    ),
                  }}
                  dimensionType={range.dimension.type}
                  selected={range.selectedKeys}
                  setSelected={(selectedKeys) =>
                    setSelections((selections) =>
                      selections.map((r) =>
                        r.dimension === range.dimension ? {...r, selectedKeys} : r,
                      ),
                    )
                  }
                  partitionDefinitionName={
                    displayedPartitionDefinition?.name ||
                    displayedBaseAsset?.partitionDefinition?.dimensionTypes.find(
                      (d) => d.name === range.dimension.name,
                    )?.dynamicPartitionsDefinitionName
                  }
                  repoAddress={repoAddress}
                  refetch={refetch}
                />

                {target.type === 'pureWithAnchorAsset' && (
                  <Alert
                    key="alert"
                    intent="info"
                    title="Dagster will materialize all partitions downstream of the selected partitions for the selected assets, using separate runs as needed."
                  />
                )}
              </Box>
            ))}
          </ToggleableSection>
        )}
        <ToggleableSection
          title={
            <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
              <Subheading>Tags</Subheading>
              <span>{tags.length} tags</span>
            </Box>
          }
          isInitiallyOpen={false}
        >
          <Box padding={{vertical: 16, horizontal: 20}} flex={{direction: 'column', gap: 12}}>
            <TagEditor
              tagsFromSession={tags}
              onChange={setTags}
              open={tagEditorOpen}
              onRequestClose={() => setTagEditorOpen(false)}
            />
            <div>Tags will be applied to all backfill runs</div>
            {tags.length ? (
              <TagContainer
                tagsFromSession={tags}
                onRequestEdit={() => setTagEditorOpen(true)}
                actions={[
                  {
                    label: 'Remove',
                    onClick: (tag) => {
                      setTags(tags.filter((t) => t.key !== tag.key));
                    },
                  },
                ]}
              />
            ) : null}
            <div>
              <Button onClick={() => setTagEditorOpen(true)}>
                {`${tags.length ? 'Edit' : 'Add'} tags`}
              </Button>
            </div>
          </Box>
        </ToggleableSection>
        <ToggleableSection
          title={<Subheading data-testid={testId('backfill-options')}>Backfill options</Subheading>}
          isInitiallyOpen={true}
        >
          {target.type === 'job' && (
            <Box padding={{vertical: 16, horizontal: 20}} flex={{direction: 'column', gap: 12}}>
              <Checkbox
                data-testid={testId('missing-only-checkbox')}
                label="Backfill only failed and missing partitions within selection"
                checked={missingFailedOnly}
                disabled={launchWithRangesAsTags}
                onChange={() => setMissingFailedOnly(!missingFailedOnly)}
              />
              {showSingleRunBackfillToggle ? (
                <RadioContainer>
                  <Subheading>Launch as...</Subheading>
                  <Radio
                    data-testid={testId('ranges-as-tags-true-radio')}
                    checked={canLaunchWithRangesAsTags && launchWithRangesAsTags}
                    disabled={!canLaunchWithRangesAsTags}
                    onChange={() => setLaunchWithRangesAsTags(!launchWithRangesAsTags)}
                  >
                    <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
                      <span>Single run</span>
                      <Tooltip
                        targetTagName="div"
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
                  </Radio>
                  <Radio
                    data-testid={testId('ranges-as-tags-false-radio')}
                    checked={!canLaunchWithRangesAsTags || !launchWithRangesAsTags}
                    disabled={!canLaunchWithRangesAsTags}
                    onChange={() => setLaunchWithRangesAsTags(!launchWithRangesAsTags)}
                  >
                    Multiple runs (One per selected partition)
                  </Radio>
                </RadioContainer>
              ) : null}
            </Box>
          )}
        </ToggleableSection>

        <Box padding={{horizontal: 20}}>
          {previewCount > 0 && (
            <Box
              margin={{top: 16}}
              flex={{direction: 'column', gap: 8}}
              padding={{vertical: 16, horizontal: 20}}
              border="top-and-bottom"
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
        </Box>
      </div>

      <DialogFooter
        topBorder
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
  displayedPartitionDefinition?: PartitionDefinitionForLaunchAssetFragment;
}> = ({upstreamAssetKeys, selections, setSelections}) => {
  // We want to warn if an immediately upstream asset 1) has the same partitioning and
  // 2) is missing materializations for keys in `allSelected`. We only offer this feature
  // for single-dimensional partitioned assets because it's difficult to express the
  // unavailable partitions in the multi-dimensional case and our "two range inputs" won't
  // allow us to remove missing individual pairs.
  const upstreamAssetHealth = usePartitionHealthData(upstreamAssetKeys);
  if (upstreamAssetHealth.length === 0) {
    return null;
  }

  const upstreamUnavailable = (singleDimensionKey: string) =>
    upstreamAssetHealth.some((a) => {
      // If the key is not undefined, it's present in the partition key space of the asset
      return (
        a.dimensions.length && a.stateForKey([singleDimensionKey]) === AssetPartitionStatus.MISSING
      );
    });

  const upstreamUnavailableSpans =
    selections.length === 1
      ? assembleIntoSpans(selections[0]!.selectedKeys, upstreamUnavailable).filter(
          (s) => s.status === true,
        )
      : [];

  if (upstreamUnavailableSpans.length === 0) {
    return null;
  }

  const onRemoveUpstreamUnavailable = () => {
    if (selections.length > 1) {
      throw new Error('Assertion failed, this feature is only available for 1 dimensional assets');
    }
    const selection = selections[0]!;
    setSelections([
      {...selection, selectedKeys: reject(selection.selectedKeys, upstreamUnavailable)},
    ]);
  };

  return (
    <Alert
      intent="warning"
      title="Upstream data missing"
      description={
        <>
          {upstreamUnavailableSpans
            .map((span) => stringForSpan(span, selections[0]!.selectedKeys))
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
  );
};

export const LAUNCH_ASSET_WARNINGS_QUERY = gql`
  query LaunchAssetWarningsQuery($upstreamAssetKeys: [AssetKeyInput!]!) {
    assetNodes(assetKeys: $upstreamAssetKeys) {
      id
      isSource
      assetKey {
        path
      }
      partitionDefinition {
        description
        dimensionTypes {
          __typename
          name
          dynamicPartitionsDefinitionName
        }
      }
    }
    instance {
      id
      ...DaemonNotRunningAlertInstanceFragment
      ...UsingDefaultLauncherAlertInstanceFragment
    }
  }

  ${DAEMON_NOT_RUNNING_ALERT_INSTANCE_FRAGMENT}
  ${USING_DEFAULT_LAUNCHER_ALERT_INSTANCE_FRAGMENT}
`;

const Warnings: React.FC<{
  launchAsBackfill: boolean;
  upstreamAssetKeys: AssetKey[];
  selections: PartitionDimensionSelection[];
  setSelections: (next: PartitionDimensionSelection[]) => void;
  displayedPartitionDefinition?: PartitionDefinitionForLaunchAssetFragment | null;
}> = ({
  launchAsBackfill,
  upstreamAssetKeys,
  selections,
  setSelections,
  displayedPartitionDefinition,
}) => {
  const warningsResult = useQuery<LaunchAssetWarningsQuery, LaunchAssetWarningsQueryVariables>(
    LAUNCH_ASSET_WARNINGS_QUERY,
    {variables: {upstreamAssetKeys}},
  );

  const instance = warningsResult.data?.instance;
  const upstreamAssets = warningsResult.data?.assetNodes;
  const upstreamAssetKeysSamePartitioning = React.useMemo(
    () =>
      (upstreamAssets || [])
        .filter(
          (a) =>
            !a.isSource &&
            a.partitionDefinition &&
            displayedPartitionDefinition &&
            partitionDefinitionsEqual(a.partitionDefinition, displayedPartitionDefinition),
        )
        .map((a) => a.assetKey),
    [upstreamAssets, displayedPartitionDefinition],
  );

  const alerts = [
    UpstreamUnavailableWarning({
      upstreamAssetKeys: upstreamAssetKeysSamePartitioning,
      selections,
      setSelections,
    }),
    instance && launchAsBackfill && DaemonNotRunningAlert({instance}),
    instance && launchAsBackfill && UsingDefaultLauncherAlert({instance}),
  ]
    .filter((a) => !!a)
    .map((a, index) => <Box key={index}>{a}</Box>);

  if (!instance || !alerts.length) {
    return null;
  }

  return (
    <ToggleableSection
      background={Colors.Yellow50}
      isInitiallyOpen={false}
      title={
        <Box
          flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
          style={{color: Colors.Yellow700}}
        >
          <Box flex={{alignItems: 'center', gap: 12}}>
            <Icon name="warning" color={Colors.Yellow700} />
            <Subheading>Warnings</Subheading>
          </Box>
          <span>{alerts.length > 1 ? `${alerts.length} warnings` : `1 warning`}</span>
        </Box>
      }
    >
      <Box flex={{direction: 'column', gap: 16}} padding={{vertical: 12, horizontal: 20}}>
        {alerts}
      </Box>
    </ToggleableSection>
  );
};
