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
} from '@dagster-io/ui';
import reject from 'lodash/reject';
import React from 'react';
import {useHistory} from 'react-router-dom';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PipelineRunTag} from '../app/ExecutionSessionStorage';
import {usePermissionsForLocation} from '../app/Permissions';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {displayNameForAssetKey, isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {PartitionHealthSummary} from '../assets/PartitionHealthSummary';
import {AssetKey} from '../assets/types';
import {LaunchBackfillParams} from '../graphql/types';
import {LAUNCH_PARTITION_BACKFILL_MUTATION} from '../instance/BackfillUtils';
import {
  LaunchPartitionBackfillMutation,
  LaunchPartitionBackfillMutationVariables,
} from '../instance/types/BackfillUtils.types';
import {CONFIG_PARTITION_SELECTION_QUERY} from '../launchpad/ConfigEditorConfigPicker';
import {useLaunchPadHooks} from '../launchpad/LaunchpadHooksContext';
import {TagContainer, TagEditor} from '../launchpad/TagEditor';
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
import {PartitionStateCheckboxes} from '../partitions/PartitionStateCheckboxes';
import {PartitionState} from '../partitions/PartitionStatus';
import {assembleIntoSpans, stringForSpan} from '../partitions/SpanRepresentation';
import {RepoAddress} from '../workspace/types';

import {executionParamsForAssetJob} from './LaunchAssetExecutionButton';
import {explodePartitionKeysInSelection, mergedAssetHealth} from './MultipartitioningSupport';
import {RunningBackfillsNotice} from './RunningBackfillsNotice';
import {PartitionDefinitionForLaunchAssetFragment} from './types/LaunchAssetExecutionButton.types';
import {usePartitionDimensionSelections} from './usePartitionDimensionSelections';
import {PartitionDimensionSelection, usePartitionHealthData} from './usePartitionHealthData';
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

  const [tagEditorOpen, setTagEditorOpen] = React.useState<boolean>(false);
  const [tags, setTags] = React.useState<PipelineRunTag[]>([]);

  const [previewCount, setPreviewCount] = React.useState(0);
  const morePreviewsCount = partitionedAssets.length - previewCount;

  const assetHealth = usePartitionHealthData(partitionedAssets.map((a) => a.assetKey));
  const mergedHealth = React.useMemo(() => mergedAssetHealth(assetHealth), [assetHealth]);

  const knownDimensions = partitionedAssets[0].partitionDefinition?.dimensionTypes || [];
  const [selections, setSelections] = usePartitionDimensionSelections({
    knownDimensionNames: knownDimensions.map((d) => d.name),
    modifyQueryString: false,
    assetHealth: mergedHealth,
  });

  const [stateFilters, setStateFilters] = React.useState<PartitionState[]>([
    PartitionState.MISSING,
  ]);

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
        const state = mergedHealth.stateForKey(dimensionKeys);
        return state === PartitionState.SUCCESS_MISSING ? PartitionState.MISSING : state;
      }),
    [selections, mergedHealth],
  );

  const keysFiltered = React.useMemo(
    () => keysInSelection.filter((key) => stateFilters.includes(key.state)),
    [keysInSelection, stateFilters],
  );

  const client = useApolloClient();
  const history = useHistory();
  const {useLaunchWithTelemetry} = useLaunchPadHooks();
  const launchWithTelemetry = useLaunchWithTelemetry();

  const instanceResult = useQuery(LAUNCH_ASSET_CHOOSE_PARTITIONS_QUERY);
  const instance = instanceResult.data?.instance;

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

    if (keysFiltered.length === 1) {
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

      const allTags = [...partition.tagsOrError.results, ...tags];
      const runConfigData = partition.runConfigOrError.yaml || '';

      const result = await launchWithTelemetry(
        {
          executionParams: {
            ...executionParamsForAssetJob(repoAddress, assetJobName, assets, allTags),
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
            partitionNames: keysFiltered.map((k) => k.partitionKey),
            fromFailure: false,
            tags,
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

          {selections.map((range, idx) => (
            <DimensionRangeWizard
              key={range.dimension.name}
              partitionKeys={range.dimension.partitionKeys}
              partitionStateForKey={(dimensionKey) =>
                mergedHealth.stateForSingleDimension(
                  idx,
                  dimensionKey,
                  selections.length === 2 ? selections[1 - idx].selectedKeys : undefined,
                )
              }
              selected={range.selectedKeys}
              setSelected={(selectedKeys) =>
                setSelections(
                  selections.map((r) =>
                    r.dimension === range.dimension ? {...r, selectedKeys} : r,
                  ),
                )
              }
            />
          ))}
          <PartitionStateCheckboxes
            partitionKeysForCounts={keysInSelection}
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
                selections={selections}
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
                  {keysFiltered.length > 1 ? 'Add tags to backfill runs' : 'Add tags'}
                </Button>
              </div>
            )}
          </Section>

          {instance && keysFiltered.length > 1 && <DaemonNotRunningAlert instance={instance} />}

          {instance && keysFiltered.length > 1 && <UsingDefaultLauncherAlert instance={instance} />}
        </Box>
      </DialogBody>

      <DialogFooter
        left={partitionSet && <RunningBackfillsNotice partitionSetName={partitionSet.name} />}
      >
        <Button intent="none" onClick={() => setOpen(false)}>
          Cancel
        </Button>
        {keysFiltered.length !== 1 && !canLaunchPartitionBackfill.enabled ? (
          <Tooltip content={canLaunchPartitionBackfill.disabledReason}>
            <Button disabled>{`Launch ${keysFiltered.length}-Run Backfill`}</Button>
          </Tooltip>
        ) : (
          <Button
            intent="primary"
            onClick={onLaunch}
            disabled={keysFiltered.length === 0}
            loading={launching}
          >
            {launching
              ? 'Launching...'
              : keysFiltered.length !== 1
              ? `Launch ${keysFiltered.length}-Run Backfill`
              : `Launch 1 Run`}
          </Button>
        )}
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

const LAUNCH_ASSET_CHOOSE_PARTITIONS_QUERY = gql`
  query LaunchAssetChoosePartitionsQuery {
    instance {
      ...DaemonNotRunningAlertInstanceFragment
      ...UsingDefaultLauncherAlertInstanceFragment
    }
  }

  ${DAEMON_NOT_RUNNING_ALERT_INSTANCE_FRAGMENT}
  ${USING_DEFAULT_LAUNCH_ERALERT_INSTANCE_FRAGMENT}
`;
