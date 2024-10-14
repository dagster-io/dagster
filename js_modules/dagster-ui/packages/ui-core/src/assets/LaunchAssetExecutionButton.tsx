import {
  Box,
  Button,
  Icon,
  Menu,
  MenuItem,
  Popover,
  Spinner,
  Tooltip,
} from '@dagster-io/ui-components';
import pick from 'lodash/pick';
import uniq from 'lodash/uniq';
import React, {useContext, useState} from 'react';
import {Link} from 'react-router-dom';
import {MaterializeButton} from 'shared/assets/MaterializeButton.oss';
import {useLaunchWithTelemetry} from 'shared/launchpad/useLaunchWithTelemetry.oss';

import {ASSET_NODE_CONFIG_FRAGMENT} from './AssetConfig';
import {
  ADDITIONAL_REQUIRED_KEYS_WARNING,
  MULTIPLE_DEFINITIONS_WARNING,
} from './AssetDefinedInMultipleReposNotice';
import {CalculateUnsyncedDialog} from './CalculateUnsyncedDialog';
import {LaunchAssetChoosePartitionsDialog} from './LaunchAssetChoosePartitionsDialog';
import {partitionDefinitionsEqual} from './MultipartitioningSupport';
import {asAssetKeyInput, getAssetCheckHandleInputs} from './asInput';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetKey} from './types';
import {
  LaunchAssetCheckUpstreamQuery,
  LaunchAssetCheckUpstreamQueryVariables,
  LaunchAssetExecutionAssetNodeFragment,
  LaunchAssetLoaderJobQuery,
  LaunchAssetLoaderJobQueryVariables,
  LaunchAssetLoaderQuery,
  LaunchAssetLoaderQueryVariables,
  LaunchAssetLoaderResourceQuery,
  LaunchAssetLoaderResourceQueryVariables,
} from './types/LaunchAssetExecutionButton.types';
import {useObserveAction} from './useObserveAction';
import {ApolloClient, gql, useApolloClient} from '../apollo-client';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {useConfirmation} from '../app/CustomConfirmationProvider';
import {IExecutionSession} from '../app/ExecutionSessionStorage';
import {DEFAULT_DISABLED_REASON} from '../app/Permissions';
import {
  displayNameForAssetKey,
  isHiddenAssetGroupJob,
  sortAssetKeys,
  tokenForAssetKey,
} from '../asset-graph/Utils';
import {PipelineSelector} from '../graphql/types';
import {AssetLaunchpad} from '../launchpad/LaunchpadRoot';
import {LaunchPipelineExecutionMutationVariables} from '../runs/types/RunUtils.types';
import {testId} from '../testing/testId';
import {CONFIG_TYPE_SCHEMA_FRAGMENT} from '../typeexplorer/ConfigTypeSchema';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

export type LaunchAssetsChoosePartitionsTarget =
  | {type: 'job'; jobName: string; assetKeys: AssetKey[]}
  | {type: 'pureWithAnchorAsset'; anchorAssetKey: AssetKey}
  | {type: 'pureAll'};

type LaunchAssetsState =
  | {type: 'none'}
  | {type: 'loading'}
  | {type: 'error'; error: string}
  | {
      type: 'launchpad';
      jobName: string;
      sessionPresets: Partial<IExecutionSession>;
      repoAddress: RepoAddress;
    }
  | {
      type: 'partitions';
      target: LaunchAssetsChoosePartitionsTarget;
      assets: LaunchAssetExecutionAssetNodeFragment[];
      upstreamAssetKeys: AssetKey[];
      repoAddress: RepoAddress;
    }
  | {
      type: 'single-run';
      executionParams: LaunchPipelineExecutionMutationVariables['executionParams'];
    };

const countIfPluralOrNotAll = (k: unknown[], all: unknown[]) =>
  k.length > 1 || (k.length > 0 && k.length !== all.length) ? ` (${k.length})` : '';

const countIfNotAll = (k: unknown[], all: unknown[]) =>
  k.length > 0 && k.length !== all.length ? ` (${k.length})` : '';

type Asset =
  | {
      assetKey: AssetKey;
      hasMaterializePermission: boolean;
      partitionDefinition: {__typename: string} | null;
      isExecutable: boolean;
      isObservable: boolean;
    }
  | {
      assetKey: AssetKey;
      hasMaterializePermission: boolean;
      isPartitioned: boolean;
      isExecutable: boolean;
      isObservable: boolean;
    };

export type AssetsInScope = {all: Asset[]; skipAllTerm?: boolean} | {selected: Asset[]};

type LaunchOption = {
  assetKeys: AssetKey[];
  label: string;
  disabledReason: string | null;
  icon: JSX.Element;
};

const isAnyPartitioned = (assets: Asset[]) =>
  assets.some(
    (a) =>
      ('partitionDefinition' in a && !!a.partitionDefinition) ||
      ('isPartitioned' in a && a.isPartitioned),
  );

export const ERROR_INVALID_ASSET_SELECTION =
  `Assets can only be materialized together if they are defined in` +
  ` the same code location and share a partition space, or form a connected` +
  ` graph in which root assets share the same partitioning.`;

export function optionsForExecuteButton(
  assets: Asset[],
  {skipAllTerm, isSelection}: {skipAllTerm?: boolean; isSelection?: boolean},
): {materializeOption: LaunchOption; observeOption: LaunchOption} {
  const materializable = assets.filter((a) => !a.isObservable && a.isExecutable);
  const observable = assets.filter((a) => a.isObservable && a.isExecutable);
  const ellipsis = isAnyPartitioned(materializable) ? '…' : '';

  return {
    materializeOption: {
      assetKeys: materializable.map((a) => a.assetKey),
      disabledReason: assets.some((a) => !a.hasMaterializePermission)
        ? 'You do not have permission to materialize assets'
        : assets.every((a) => !a.isExecutable)
        ? 'External assets cannot be materialized'
        : assets.every((a) => a.isObservable)
        ? 'Observable assets cannot be materialized'
        : materializable.length === 0
        ? 'No executable assets selected.'
        : null,
      icon: <Icon name="materialization" />,
      label: isSelection
        ? `Materialize selected${countIfPluralOrNotAll(materializable, assets)}${ellipsis}`
        : materializable.length > 1 && !skipAllTerm
        ? `Materialize all${countIfNotAll(materializable, assets)}${ellipsis}`
        : `Materialize${countIfNotAll(materializable, assets)}${ellipsis}`,
    },
    observeOption: {
      assetKeys: observable.map((a) => a.assetKey),
      disabledReason: assets.some((a) => !a.hasMaterializePermission)
        ? 'You do not have permission to observe assets'
        : observable.length === 0
        ? 'Assets do not have observation functions'
        : null,
      icon: <Icon name="observation" />,
      label: isSelection
        ? `Observe selected${countIfPluralOrNotAll(observable, assets)}`
        : observable.length > 1 && !skipAllTerm
        ? `Observe all${countIfNotAll(observable, assets)}`
        : `Observe${countIfNotAll(observable, assets)}`,
    },
  };
}

export const LaunchAssetExecutionButton = ({
  scope,
  preferredJobName,
  additionalDropdownOptions,
  primary = true,
  showChangedAndMissingOption = true,
}: {
  scope: AssetsInScope;
  showChangedAndMissingOption?: boolean;
  primary?: boolean;
  preferredJobName?: string;
  additionalDropdownOptions?: (
    | JSX.Element
    | {
        label: string;
        icon?: JSX.Element;
        onClick: () => void;
        disabled?: boolean;
      }
  )[];
}) => {
  const materialize = useMaterializationAction(preferredJobName);
  const observe = useObserveAction(preferredJobName);
  const loading = materialize.loading || observe.loading;

  const [isOpen, setIsOpen] = useState(false);
  const [showCalculatingUnsyncedDialog, setShowCalculatingUnsyncedDialog] = useState(false);

  const {
    featureContext: {canSeeMaterializeAction},
  } = useContext(CloudOSSContext);

  if (!canSeeMaterializeAction) {
    return null;
  }
  const [assets, {materializeOption, observeOption}] =
    'selected' in scope
      ? [scope.selected, optionsForExecuteButton(scope.selected, {isSelection: true})]
      : [scope.all, optionsForExecuteButton(scope.all, {skipAllTerm: scope.skipAllTerm})];

  const [firstOption, firstAction, secondOption, secondAction] =
    materializeOption.disabledReason && !observeOption.disabledReason
      ? [observeOption, observe.onClick, materializeOption, materialize.onClick]
      : [materializeOption, materialize.onClick, observeOption, observe.onClick];

  if (firstOption.disabledReason) {
    return (
      <Tooltip content={firstOption.disabledReason} position="bottom-right">
        <Button
          intent={primary ? 'primary' : undefined}
          icon={firstOption.icon}
          data-testid={testId('materialize-button')}
          disabled
        >
          {firstOption.label}
        </Button>
      </Tooltip>
    );
  }

  return (
    <>
      <CalculateUnsyncedDialog
        assets={assets}
        isOpen={showCalculatingUnsyncedDialog}
        onClose={() => setShowCalculatingUnsyncedDialog(false)}
        onMaterializeAssets={materialize.onClick}
      />
      <Box flex={{alignItems: 'center'}}>
        <Tooltip
          content="Shift+click to add configuration"
          placement="left"
          useDisabledButtonTooltipFix
        >
          <MaterializeButton
            intent={primary ? 'primary' : undefined}
            data-testid={testId('materialize-button')}
            onClick={(e) => firstAction(firstOption.assetKeys, e)}
            style={{
              borderTopRightRadius: 0,
              borderBottomRightRadius: 0,
              borderRight: `1px solid rgba(255,255,255,0.2)`,
            }}
            disabled={!firstOption.assetKeys.length}
            icon={loading ? <Spinner purpose="body-text" /> : <Icon name="materialization" />}
          >
            {firstOption.label}
          </MaterializeButton>
        </Tooltip>

        <Popover
          isOpen={isOpen}
          onInteraction={(nextOpen) => setIsOpen(nextOpen)}
          position="bottom-right"
          content={
            <Menu>
              <Tooltip
                canShow={!!secondOption.disabledReason}
                content={secondOption.disabledReason || ''}
                useDisabledButtonTooltipFix
                position="left"
              >
                <MenuItem
                  key={secondOption.label}
                  text={secondOption.label}
                  icon={secondOption.icon}
                  data-testid={testId('materialize-secondary-option')}
                  disabled={secondOption.assetKeys.length === 0}
                  onClick={(e) => secondAction(secondOption.assetKeys, e)}
                />
              </Tooltip>
              {showChangedAndMissingOption ? (
                <MenuItem
                  text="Materialize unsynced"
                  icon="changes_present"
                  disabled={!!materializeOption.disabledReason}
                  onClick={() => setShowCalculatingUnsyncedDialog(true)}
                />
              ) : null}
              <MenuItem
                text="Open launchpad"
                icon="open_in_new"
                onClick={(e: React.MouseEvent<any>) => {
                  materialize.onClick(firstOption.assetKeys, e, true);
                }}
              />
              {additionalDropdownOptions?.map((option) => {
                if (!('label' in option)) {
                  return option;
                }

                const item = (
                  <MenuItem
                    key={option.label}
                    text={option.label}
                    icon={option.icon}
                    onClick={option.onClick}
                    disabled={option.disabled}
                  />
                );

                return option.disabled ? (
                  <Tooltip key={option.label} content={DEFAULT_DISABLED_REASON} placement="left">
                    {item}
                  </Tooltip>
                ) : (
                  item
                );
              })}
            </Menu>
          }
        >
          <Button
            role="button"
            data-testid={testId('materialize-button-dropdown')}
            style={{minWidth: 'initial', borderTopLeftRadius: 0, borderBottomLeftRadius: 0}}
            icon={<Icon name="arrow_drop_down" />}
            disabled={false}
            intent={primary ? 'primary' : undefined}
          />
        </Popover>
      </Box>
      {materialize.launchpadElement}
    </>
  );
};

export const useMaterializationAction = (preferredJobName?: string) => {
  const launchWithTelemetry = useLaunchWithTelemetry();

  const client = useApolloClient();
  const confirm = useConfirmation();

  const [state, setState] = React.useState<LaunchAssetsState>({type: 'none'});

  const onLoad = async (
    assetKeysOrJob: AssetKey[] | PipelineSelector,
  ): Promise<LaunchAssetLoaderQuery | LaunchAssetLoaderJobQuery> => {
    const result =
      assetKeysOrJob instanceof Array
        ? await client.query<LaunchAssetLoaderQuery, LaunchAssetLoaderQueryVariables>({
            query: LAUNCH_ASSET_LOADER_QUERY,
            variables: {assetKeys: assetKeysOrJob.map(asAssetKeyInput)},
          })
        : await client.query<LaunchAssetLoaderJobQuery, LaunchAssetLoaderJobQueryVariables>({
            query: LAUNCH_ASSET_LOADER_JOB_QUERY,
            variables: {job: assetKeysOrJob},
          });
    return result.data;
  };

  const onClick = async (
    assetKeysOrJob: AssetKey[] | PipelineSelector,
    e: React.MouseEvent<any>,
    _forceLaunchpad = false,
  ) => {
    if (state.type === 'loading') {
      return;
    }
    setState({type: 'loading'});

    let data = await onLoad(assetKeysOrJob);

    if ('assetNodeDefinitionCollisions' in data && data.assetNodeDefinitionCollisions.length) {
      showCustomAlert(buildAssetCollisionsAlert(data));
      setState({type: 'none'});
      return;
    }

    if ('assetNodeAdditionalRequiredKeys' in data && data.assetNodeAdditionalRequiredKeys.length) {
      try {
        await confirm(buildAssetAdditionalRequiredKeysAlert(data));
      } catch {
        setState({type: 'none'});
        return; // user declined confirm
      }
      if (assetKeysOrJob instanceof Array) {
        data = await onLoad([...assetKeysOrJob, ...data.assetNodeAdditionalRequiredKeys]);
      }
    }

    const assets = data.assetNodes;
    const forceLaunchpad = e.shiftKey || _forceLaunchpad;

    const next = await stateForLaunchingAssets(client, assets, forceLaunchpad, preferredJobName);
    if (next.type === 'error') {
      showCustomAlert({title: 'Unable to Materialize', body: next.error});
      setState({type: 'none'});
      return;
    }

    const missing = await upstreamAssetsWithNoMaterializations(client, assets);
    if (missing.length) {
      try {
        await confirm(buildUpstreamAssetsWithNoMaterializationsAlert(missing));
      } catch {
        setState({type: 'none'});
        return; // user declined confirm
      }
    }

    if (next.type === 'single-run') {
      await launchWithTelemetry({executionParams: next.executionParams}, 'toast');
      setState({type: 'none'});
    } else {
      setState(next);
    }
  };

  const launchpad = () => {
    if (state.type === 'launchpad') {
      return (
        <AssetLaunchpad
          assetJobName={state.jobName}
          repoAddress={state.repoAddress}
          sessionPresets={state.sessionPresets}
          open={true}
          setOpen={() => setState({type: 'none'})}
        />
      );
    }

    if (state.type === 'partitions') {
      return (
        <LaunchAssetChoosePartitionsDialog
          assets={state.assets}
          upstreamAssetKeys={state.upstreamAssetKeys}
          repoAddress={state.repoAddress}
          target={state.target}
          open={true}
          setOpen={() => setState({type: 'none'})}
          refetch={async () => {
            const {assetNodes} = await onLoad(state.assets.map(asAssetKeyInput));
            const next = await stateForLaunchingAssets(client, assetNodes, false, preferredJobName);
            if (next.type === 'error') {
              showCustomAlert({
                title: 'Unable to Materialize',
                body: next.error,
              });
              setState({type: 'none'});
              return;
            }
            setState(next);
          }}
        />
      );
    }

    return null;
  };

  return {onClick, loading: state.type === 'loading', launchpadElement: launchpad()};
};

async function stateForLaunchingAssets(
  client: ApolloClient<any>,
  assets: LaunchAssetExecutionAssetNodeFragment[],
  forceLaunchpad: boolean,
  preferredJobName?: string,
): Promise<LaunchAssetsState> {
  if (assets.some((x) => x.isObservable)) {
    return {
      type: 'error',
      error: 'One or more observable assets are selected and cannot be materialized.',
    };
  }
  if (assets.some((x) => !x.isExecutable)) {
    return {
      type: 'error',
      error: 'One or more external assets are selected.',
    };
  }

  const repoAddress = buildRepoAddress(
    assets[0]?.repository.name || '',
    assets[0]?.repository.location.name || '',
  );
  const jobName = getCommonJob(assets, preferredJobName);
  const partitionDefinition = assets.find((a) => !!a.partitionDefinition)?.partitionDefinition;

  const inSameRepo = assets.every(
    (a) =>
      a.repository.name === repoAddress.name && a.repository.location.name === repoAddress.location,
  );
  const inSameOrNoPartitionSpace = assets.every(
    (a) =>
      !a.partitionDefinition ||
      !partitionDefinition ||
      partitionDefinitionsEqual(a.partitionDefinition, partitionDefinition),
  );

  if (!inSameRepo || !inSameOrNoPartitionSpace || !jobName) {
    if (!partitionDefinition) {
      return {type: 'error', error: ERROR_INVALID_ASSET_SELECTION};
    }
    const anchorAsset = getAnchorAssetForPartitionMappedBackfill(assets);
    if (!anchorAsset) {
      return {
        type: 'partitions',
        assets,
        target: {type: 'pureAll'},
        upstreamAssetKeys: [],
        repoAddress,
      };
    }
    return {
      type: 'partitions',
      assets,
      target: {type: 'pureWithAnchorAsset', anchorAssetKey: anchorAsset.assetKey},
      upstreamAssetKeys: getUpstreamAssetKeys(assets),
      repoAddress,
    };
  }

  const resourceResult = await client.query<
    LaunchAssetLoaderResourceQuery,
    LaunchAssetLoaderResourceQueryVariables
  >({
    query: LAUNCH_ASSET_LOADER_RESOURCE_QUERY,
    variables: {
      pipelineName: jobName,
      repositoryName: assets[0]!.repository.name,
      repositoryLocationName: assets[0]!.repository.location.name,
    },
  });
  const pipeline = resourceResult.data.pipelineOrError;
  if (pipeline.__typename !== 'Pipeline') {
    return {type: 'error', error: pipeline.message};
  }
  const requiredResourceKeys = assets.flatMap((a) => a.requiredResources.map((r) => r.resourceKey));
  const resources = pipeline.modes[0]!.resources.filter((r) =>
    requiredResourceKeys.includes(r.name),
  );
  const anyResourcesHaveRequiredConfig = resources.some((r) => r.configField?.isRequired);
  const anyAssetsHaveRequiredConfig = assets.some((a) => a.configField?.isRequired);

  // Note: If a partition definition is present and we're launching a user-defined job,
  // we assume that any required config will be provided by a PartitionedConfig function
  // attached to the job. Otherwise backfills won't work and you'll know to add one!
  const assumeConfigPresent = partitionDefinition && !isHiddenAssetGroupJob(jobName);

  const needLaunchpad =
    !assumeConfigPresent && (anyAssetsHaveRequiredConfig || anyResourcesHaveRequiredConfig);

  if (needLaunchpad || forceLaunchpad) {
    const assetOpNames = assets.flatMap((a) => a.opNames || []);
    return {
      type: 'launchpad',
      jobName,
      repoAddress,
      sessionPresets: {
        flattenGraphs: true,
        assetSelection: assets.map((a) => ({assetKey: a.assetKey, opNames: a.opNames})),
        assetChecksAvailable: assets.flatMap((a) =>
          a.assetChecksOrError.__typename === 'AssetChecks'
            ? a.assetChecksOrError.checks
                // For user code prior to 1.5.10 jobNames isn't populated, so don't filter on it
                .filter((check) => check.jobNames.length === 0 || check.jobNames.includes(jobName))
                .map((check) => ({...check, assetKey: a.assetKey}))
            : [],
        ),
        includeSeparatelyExecutableChecks: true,
        solidSelectionQuery: assetOpNames.map((name) => `"${name}"`).join(', '),
        base: partitionDefinition
          ? {type: 'asset-job-partition', partitionName: null, tags: []}
          : undefined,
      },
    };
  }
  if (partitionDefinition) {
    return {
      type: 'partitions',
      assets,
      target: {type: 'job', jobName, assetKeys: assets.map(asAssetKeyInput)},
      upstreamAssetKeys: getUpstreamAssetKeys(assets),
      repoAddress,
    };
  }
  return {
    type: 'single-run',
    executionParams: executionParamsForAssetJob(repoAddress, jobName, assets, []),
  };
}

export function getCommonJob(
  assets: LaunchAssetExecutionAssetNodeFragment[],
  preferredJobName?: string,
) {
  const everyAssetHasJob = (jobName: string) => assets.every((a) => a.jobNames.includes(jobName));
  const jobsInCommon = assets[0] ? assets[0].jobNames.filter(everyAssetHasJob) : [];
  return jobsInCommon.find((name) => name === preferredJobName) || jobsInCommon[0] || null;
}

function getAnchorAssetForPartitionMappedBackfill(assets: LaunchAssetExecutionAssetNodeFragment[]) {
  // We have the ability to launch a pure asset backfill which will infer the partitions
  // of downstream assets IFF the selection's root assets (at the top of the tree) ALL
  // share a partition definition

  // First, get the roots of the selection. The root assets are the ones with none
  // of their dependencyKeys selected.
  const roots = assets.filter((a) => {
    const aDeps = a.dependencyKeys.map(tokenForAssetKey);
    return !assets.some((b) => aDeps.includes(tokenForAssetKey(b.assetKey)));
  });

  const partitionedRoots = roots
    .filter((r) => !!r.partitionDefinition)
    .sort((a, b) => sortAssetKeys(a.assetKey, b.assetKey));

  if (!partitionedRoots.length) {
    return null;
  }

  // Next, see if they all share a partition set. If they do, any random root can be
  // the anchor asset but we do it alphabetically so that it is deterministic.
  const first = partitionedRoots[0];
  if (
    first &&
    !partitionedRoots.every((r) =>
      partitionDefinitionsEqual(first.partitionDefinition!, r.partitionDefinition!),
    )
  ) {
    return null;
  }

  return first;
}

function getUpstreamAssetKeys(assets: LaunchAssetExecutionAssetNodeFragment[]) {
  const assetKeys = new Set(assets.map((a) => JSON.stringify({path: a.assetKey.path})));
  return uniq(assets.flatMap((a) => a.dependencyKeys.map(({path}) => JSON.stringify({path}))))
    .filter((key) => !assetKeys.has(key))
    .map((key) => JSON.parse(key));
}

async function upstreamAssetsWithNoMaterializations(
  client: ApolloClient<any>,
  assets: LaunchAssetExecutionAssetNodeFragment[],
) {
  const upstreamAssetKeys = getUpstreamAssetKeys(assets);
  if (upstreamAssetKeys.length === 0) {
    return [];
  }

  const result = await client.query<
    LaunchAssetCheckUpstreamQuery,
    LaunchAssetCheckUpstreamQueryVariables
  >({
    query: LAUNCH_ASSET_CHECK_UPSTREAM_QUERY,
    variables: {assetKeys: upstreamAssetKeys},
  });

  return result.data.assetNodes
    .filter((a) => a.isMaterializable && a.assetMaterializations.length === 0)
    .map((a) => a.assetKey);
}

export function executionParamsForAssetJob(
  repoAddress: RepoAddress,
  jobName: string,
  assets: Pick<
    LaunchAssetExecutionAssetNodeFragment,
    'assetKey' | 'opNames' | 'assetChecksOrError'
  >[],
  tags: {key: string; value: string}[],
): LaunchPipelineExecutionMutationVariables['executionParams'] {
  return {
    mode: 'default',
    executionMetadata: {
      tags: tags.map((t) => pick(t, ['key', 'value'])),
    },
    runConfigData: '{}',
    selector: {
      repositoryLocationName: repoAddress.location,
      repositoryName: repoAddress.name,
      pipelineName: jobName,
      assetSelection: assets.map(asAssetKeyInput),
      assetCheckSelection: getAssetCheckHandleInputs(assets, jobName),
    },
  };
}

export function buildAssetCollisionsAlert(data: LaunchAssetLoaderQuery) {
  return {
    title: MULTIPLE_DEFINITIONS_WARNING,
    body: (
      <div style={{overflow: 'auto'}}>
        One or more of the selected assets are defined in multiple code locations. Rename these
        assets to avoid collisions and then try again.
        <ul>
          {data.assetNodeDefinitionCollisions.map((collision, idx) => (
            <li key={idx}>
              <Link to={assetDetailsPathForKey(collision.assetKey)} target="_blank">
                <strong>{displayNameForAssetKey(collision.assetKey)}</strong>
              </Link>
              <ul>
                {collision.repositories.map((r, ridx) => (
                  <li key={ridx}>
                    {repoAddressAsHumanString({name: r.name, location: r.location.name})}
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      </div>
    ),
  };
}

export function buildAssetAdditionalRequiredKeysAlert(data: LaunchAssetLoaderQuery) {
  return {
    catchOnCancel: true,
    title: ADDITIONAL_REQUIRED_KEYS_WARNING,
    description: (
      <div style={{overflow: 'auto'}}>
        One or more of the selected assets are part of a multi-asset that does not support
        subsetting or that has required outputs outside the current selection. Materializing the
        current selection will also yield new materializations for the following:
        <ul>
          {data.assetNodeAdditionalRequiredKeys.map((assetKey, idx) => (
            <li key={idx}>
              <Link to={assetDetailsPathForKey(assetKey, {view: 'definition'})} target="_blank">
                <strong>{displayNameForAssetKey(assetKey)}</strong>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    ),
  };
}
export function buildUpstreamAssetsWithNoMaterializationsAlert(missing: AssetKey[]) {
  return {
    catchOnCancel: true,
    title: 'Are you sure?',
    description: (
      <>
        <div>
          Materializing these assets may fail because the upstream assets listed below have not been
          materialized yet.
        </div>
        <ul>
          {missing.map((assetKey, idx) => (
            <li key={idx}>{displayNameForAssetKey(assetKey)}</li>
          ))}
        </ul>
      </>
    ),
  };
}

const PARTITION_DEFINITION_FOR_LAUNCH_ASSET_FRAGMENT = gql`
  fragment PartitionDefinitionForLaunchAssetFragment on PartitionDefinition {
    description
    type
    name
    dimensionTypes {
      name
      dynamicPartitionsDefinitionName
    }
  }
`;

const BACKFILL_POLICY_FOR_LAUNCH_ASSET_FRAGMENT = gql`
  fragment BackfillPolicyForLaunchAssetFragment on BackfillPolicy {
    maxPartitionsPerRun
    description
    policyType
  }
`;

const LAUNCH_ASSET_EXECUTION_ASSET_NODE_FRAGMENT = gql`
  fragment LaunchAssetExecutionAssetNodeFragment on AssetNode {
    id
    opNames
    jobNames
    graphName
    hasMaterializePermission
    partitionDefinition {
      ...PartitionDefinitionForLaunchAssetFragment
    }
    backfillPolicy {
      ...BackfillPolicyForLaunchAssetFragment
    }
    isObservable
    isExecutable
    isMaterializable
    assetKey {
      path
    }
    assetChecksOrError {
      ... on AssetChecks {
        checks {
          name
          canExecuteIndividually
          jobNames
        }
      }
    }
    dependencyKeys {
      path
    }
    repository {
      id
      name
      location {
        id
        name
      }
    }
    requiredResources {
      resourceKey
    }
    ...AssetNodeConfigFragment
  }

  ${ASSET_NODE_CONFIG_FRAGMENT}
  ${PARTITION_DEFINITION_FOR_LAUNCH_ASSET_FRAGMENT}
  ${BACKFILL_POLICY_FOR_LAUNCH_ASSET_FRAGMENT}
`;

export const LAUNCH_ASSET_LOADER_QUERY = gql`
  query LaunchAssetLoaderQuery($assetKeys: [AssetKeyInput!]!) {
    assetNodes(assetKeys: $assetKeys) {
      id
      ...LaunchAssetExecutionAssetNodeFragment
    }
    assetNodeAdditionalRequiredKeys(assetKeys: $assetKeys) {
      path
    }
    assetNodeDefinitionCollisions(assetKeys: $assetKeys) {
      assetKey {
        path
      }
      repositories {
        id
        name
        location {
          id
          name
        }
      }
    }
  }
  ${LAUNCH_ASSET_EXECUTION_ASSET_NODE_FRAGMENT}
`;

export const LAUNCH_ASSET_LOADER_JOB_QUERY = gql`
  query LaunchAssetLoaderJobQuery($job: PipelineSelector!) {
    assetNodes(pipeline: $job) {
      id
      ...LaunchAssetExecutionAssetNodeFragment
    }
  }
  ${LAUNCH_ASSET_EXECUTION_ASSET_NODE_FRAGMENT}
`;

export const LAUNCH_ASSET_LOADER_RESOURCE_QUERY = gql`
  query LaunchAssetLoaderResourceQuery(
    $pipelineName: String!
    $repositoryLocationName: String!
    $repositoryName: String!
  ) {
    pipelineOrError(
      params: {
        pipelineName: $pipelineName
        repositoryName: $repositoryName
        repositoryLocationName: $repositoryLocationName
      }
    ) {
      ... on PythonError {
        message
      }
      ... on InvalidSubsetError {
        message
      }
      ... on PipelineNotFoundError {
        message
      }
      ... on Pipeline {
        id
        modes {
          id
          resources {
            name
            description
            configField {
              name
              isRequired
              configType {
                ...ConfigTypeSchemaFragment
                recursiveConfigTypes {
                  ...ConfigTypeSchemaFragment
                }
              }
            }
          }
        }
      }
    }
  }

  ${CONFIG_TYPE_SCHEMA_FRAGMENT}
`;

export const LAUNCH_ASSET_CHECK_UPSTREAM_QUERY = gql`
  query LaunchAssetCheckUpstreamQuery($assetKeys: [AssetKeyInput!]!) {
    assetNodes(assetKeys: $assetKeys, loadMaterializations: true) {
      id
      assetKey {
        path
      }
      isMaterializable
      opNames
      graphName
      assetMaterializations(limit: 1) {
        runId
      }
    }
  }
`;
