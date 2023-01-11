import {ApolloClient, useApolloClient} from '@apollo/client';
import {Box, Button, Icon, Menu, MenuItem, Popover, Spinner, Tooltip} from '@dagster-io/ui';
import pick from 'lodash/pick';
import uniq from 'lodash/uniq';
import React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {useConfirmation} from '../app/CustomConfirmationProvider';
import {IExecutionSession} from '../app/ExecutionSessionStorage';
import {usePermissionsDEPRECATED} from '../app/Permissions';
import {
  displayNameForAssetKey,
  isHiddenAssetGroupJob,
  LiveData,
  toGraphId,
} from '../asset-graph/Utils';
import {graphql} from '../graphql';
import {
  LaunchAssetCheckUpstreamQueryQuery,
  LaunchAssetCheckUpstreamQueryQueryVariables,
  LaunchAssetExecutionAssetNodeFragmentFragment,
  LaunchAssetLoaderQueryQuery,
  LaunchAssetLoaderQueryQueryVariables,
  LaunchAssetLoaderResourceQueryQuery,
  LaunchAssetLoaderResourceQueryQueryVariables,
  LaunchPipelineExecutionMutationVariables,
} from '../graphql/graphql';
import {useLaunchPadHooks} from '../launchpad/LaunchpadHooksContext';
import {AssetLaunchpad} from '../launchpad/LaunchpadRoot';
import {DagsterTag} from '../runs/RunTag';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

import {MULTIPLE_DEFINITIONS_WARNING} from './AssetDefinedInMultipleReposNotice';
import {LaunchAssetChoosePartitionsDialog} from './LaunchAssetChoosePartitionsDialog';
import {isAssetMissing, isAssetStale} from './StaleTag';
import {AssetKey} from './types';

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
      jobName: string;
      assets: LaunchAssetExecutionAssetNodeFragmentFragment[];
      upstreamAssetKeys: AssetKey[];
      repoAddress: RepoAddress;
    }
  | {
      type: 'single-run';
      executionParams: LaunchPipelineExecutionMutationVariables['executionParams'];
    };

const countOrBlank = (k: unknown[]) => (k.length > 1 ? ` (${k.length})` : '');

type Asset =
  | {assetKey: AssetKey; partitionDefinition: {__typename: string} | null; isSource: boolean}
  | {assetKey: AssetKey; isPartitioned: boolean; isSource: boolean};

type AssetsInScope = {all: Asset[]; skipAllTerm?: boolean} | {selected: Asset[]};

type LaunchOption = {assetKeys: AssetKey[]; label: string};

const isAnyPartitioned = (assets: Asset[]) =>
  assets.some(
    (a) =>
      ('partitionDefinition' in a && !!a.partitionDefinition) ||
      ('isPartitioned' in a && a.isPartitioned),
  );

function optionsForButton(scope: AssetsInScope, liveDataForStale?: LiveData): LaunchOption[] {
  // If you pass a set of selected assets, we always show just one option
  // to materialize that selection.
  if ('selected' in scope) {
    const assets = scope.selected.filter((a) => !a.isSource);
    return [
      {
        assetKeys: assets.map((a) => a.assetKey),
        label: `Materialize selected${countOrBlank(assets)}${isAnyPartitioned(assets) ? '…' : ''}`,
      },
    ];
  }

  const options: LaunchOption[] = [];
  const assets = scope.all.filter((a) => !a.isSource);

  options.push({
    assetKeys: assets.map((a) => a.assetKey),
    label:
      assets.length > 1 && !scope.skipAllTerm
        ? `Materialize all${isAnyPartitioned(assets) ? '…' : ''}`
        : `Materialize${isAnyPartitioned(assets) ? '…' : ''}`,
  });

  if (liveDataForStale) {
    const missingOrStale = assets.filter(
      (a) =>
        isAssetMissing(liveDataForStale[toGraphId(a.assetKey)]) ||
        isAssetStale(liveDataForStale[toGraphId(a.assetKey)]),
    );

    options.push({
      assetKeys: missingOrStale.map((a) => a.assetKey),
      label: `Materialize stale and missing${countOrBlank(missingOrStale)}`,
    });
  }

  return options;
}

export const LaunchAssetExecutionButton: React.FC<{
  scope: AssetsInScope;
  liveDataForStale?: LiveData; // For "stale" dropdown options
  intent?: 'primary' | 'none';
  preferredJobName?: string;
}> = ({scope, liveDataForStale, preferredJobName, intent = 'primary'}) => {
  const {canLaunchPipelineExecution} = usePermissionsDEPRECATED();
  const {onClick, loading, launchpadElement} = useMaterializationAction(preferredJobName);
  const [isOpen, setIsOpen] = React.useState(false);

  const options = optionsForButton(scope, liveDataForStale);
  const firstOption = options[0];

  const {MaterializeButton} = useLaunchPadHooks();

  if (!firstOption) {
    return <span />;
  }

  if (!canLaunchPipelineExecution.enabled) {
    return (
      <Tooltip content="You do not have permission to materialize assets" position="bottom-right">
        <Button intent={intent} icon={<Icon name="materialization" />} disabled>
          {firstOption.label}
        </Button>
      </Tooltip>
    );
  }

  return (
    <>
      <Box flex={{alignItems: 'center'}}>
        <Tooltip
          content="Shift+click to add configuration"
          position="bottom-right"
          useDisabledButtonTooltipFix
        >
          <MaterializeButton
            intent={intent}
            onClick={(e) => onClick(firstOption.assetKeys, e)}
            style={
              options.length > 1
                ? {
                    borderTopRightRadius: 0,
                    borderBottomRightRadius: 0,
                    borderRight: `1px solid rgba(255,255,255,0.2)`,
                  }
                : {}
            }
            disabled={!firstOption.assetKeys.length}
            icon={loading ? <Spinner purpose="body-text" /> : <Icon name="materialization" />}
          >
            {firstOption.label}
          </MaterializeButton>
        </Tooltip>
        {options.length > 1 && (
          <Popover
            isOpen={isOpen}
            onInteraction={(nextOpen) => setIsOpen(nextOpen)}
            position="bottom-right"
            content={
              <Menu>
                {options.slice(1).map((option) => (
                  <MenuItem
                    key={option.label}
                    text={option.label}
                    icon="materialization"
                    disabled={option.assetKeys.length === 0}
                    onClick={(e) => onClick(option.assetKeys, e)}
                  />
                ))}
              </Menu>
            }
          >
            <Button
              role="button"
              style={{minWidth: 'initial', borderTopLeftRadius: 0, borderBottomLeftRadius: 0}}
              icon={<Icon name="arrow_drop_down" />}
              intent={intent}
            />
          </Popover>
        )}
      </Box>
      {launchpadElement}
    </>
  );
};

export const useMaterializationAction = (preferredJobName?: string) => {
  const {useLaunchWithTelemetry} = useLaunchPadHooks();
  const launchWithTelemetry = useLaunchWithTelemetry();

  const client = useApolloClient();
  const confirm = useConfirmation();

  const [state, setState] = React.useState<LaunchAssetsState>({type: 'none'});

  const onClick = async (assetKeys: AssetKey[], e: React.MouseEvent<any>) => {
    if (state.type === 'loading') {
      return;
    }
    setState({type: 'loading'});

    const result = await client.query<
      LaunchAssetLoaderQueryQuery,
      LaunchAssetLoaderQueryQueryVariables
    >({
      query: LAUNCH_ASSET_LOADER_QUERY,
      variables: {assetKeys: assetKeys.map(({path}) => ({path}))},
    });

    if (result.data.assetNodeDefinitionCollisions.length) {
      showCustomAlert(buildAssetCollisionsAlert(result.data));
      setState({type: 'none'});
      return;
    }

    const assets = result.data.assetNodes;
    const forceLaunchpad = e.shiftKey;

    const next = await stateForLaunchingAssets(client, assets, forceLaunchpad, preferredJobName);

    if (next.type === 'error') {
      showCustomAlert({
        title: 'Unable to Materialize',
        body: next.error,
      });
      setState({type: 'none'});
      return;
    }

    const missing = await upstreamAssetsWithNoMaterializations(client, assets);
    if (missing.length) {
      setState({type: 'none'});
      try {
        await confirm({
          title: 'Are you sure?',
          description: (
            <>
              <div>
                Materializing these assets may fail because the upstream assets listed below have
                not been materialized yet.
              </div>
              <ul>
                {missing.map((assetKey, idx) => (
                  <li key={idx}>{displayNameForAssetKey(assetKey)}</li>
                ))}
              </ul>
            </>
          ),
        });
        setState({type: 'loading'});
      } catch {
        return;
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
          assetJobName={state.jobName}
          open={true}
          setOpen={() => setState({type: 'none'})}
        />
      );
    }

    return null;
  };

  return {onClick, loading: state.type === 'loading', launchpadElement: launchpad()};
};

async function stateForLaunchingAssets(
  client: ApolloClient<any>,
  assets: LaunchAssetExecutionAssetNodeFragmentFragment[],
  forceLaunchpad: boolean,
  preferredJobName?: string,
): Promise<LaunchAssetsState> {
  if (assets.some((x) => x.isSource)) {
    return {
      type: 'error',
      error: 'One or more source assets are selected and cannot be materialized.',
    };
  }

  const repoAddress = buildRepoAddress(
    assets[0]?.repository.name || '',
    assets[0]?.repository.location.name || '',
  );
  const repoName = repoAddressAsHumanString(repoAddress);

  if (
    !assets.every(
      (a) =>
        a.repository.name === repoAddress.name &&
        a.repository.location.name === repoAddress.location,
    )
  ) {
    return {
      type: 'error',
      error: `Assets must be in ${repoName} to be materialized together.`,
    };
  }

  const partitionDefinition = assets.find((a) => !!a.partitionDefinition)?.partitionDefinition;
  if (
    assets.some(
      (a) =>
        a.partitionDefinition &&
        partitionDefinition &&
        a.partitionDefinition.description !== partitionDefinition.description,
    )
  ) {
    return {
      type: 'error',
      error: 'Assets must share a partition definition to be materialized together.',
    };
  }

  const jobName = getCommonJob(assets, preferredJobName);
  if (!jobName) {
    return {
      type: 'error',
      error: 'Assets must be in the same job to be materialized together.',
    };
  }

  const resourceResult = await client.query<
    LaunchAssetLoaderResourceQueryQuery,
    LaunchAssetLoaderResourceQueryQueryVariables
  >({
    query: LAUNCH_ASSET_LOADER_RESOURCE_QUERY,
    variables: {
      pipelineName: jobName,
      repositoryName: assets[0].repository.name,
      repositoryLocationName: assets[0].repository.location.name,
    },
  });
  const pipeline = resourceResult.data.pipelineOrError;
  if (pipeline.__typename !== 'Pipeline') {
    return {type: 'error', error: pipeline.message};
  }
  const partitionSets = resourceResult.data.partitionSetsOrError;
  if (partitionSets.__typename !== 'PartitionSets') {
    return {type: 'error', error: partitionSets.message};
  }

  const requiredResourceKeys = assets.flatMap((a) => a.requiredResources.map((r) => r.resourceKey));
  const resources = pipeline.modes[0].resources.filter((r) =>
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
        solidSelectionQuery: assetOpNames.map((name) => `"${name}"`).join(', '),
        base: partitionSets.results.length
          ? {
              partitionsSetName: partitionSets.results[0].name,
              partitionName: null,
              tags: [],
            }
          : undefined,
      },
    };
  }
  if (partitionDefinition) {
    const upstreamAssetKeys = getUpstreamAssetKeys(assets);
    return {
      type: 'partitions',
      assets,
      jobName,
      repoAddress,
      upstreamAssetKeys,
    };
  }
  return {
    type: 'single-run',
    executionParams: executionParamsForAssetJob(repoAddress, jobName, assets, []),
  };
}

export function getCommonJob(
  assets: LaunchAssetExecutionAssetNodeFragmentFragment[],
  preferredJobName?: string,
) {
  const everyAssetHasJob = (jobName: string) => assets.every((a) => a.jobNames.includes(jobName));
  const jobsInCommon = assets[0] ? assets[0].jobNames.filter(everyAssetHasJob) : [];
  return jobsInCommon.find((name) => name === preferredJobName) || jobsInCommon[0] || null;
}

function getUpstreamAssetKeys(assets: LaunchAssetExecutionAssetNodeFragmentFragment[]) {
  const assetKeys = new Set(assets.map((a) => JSON.stringify({path: a.assetKey.path})));
  return uniq(assets.flatMap((a) => a.dependencyKeys.map(({path}) => JSON.stringify({path}))))
    .filter((key) => !assetKeys.has(key))
    .map((key) => JSON.parse(key));
}

async function upstreamAssetsWithNoMaterializations(
  client: ApolloClient<any>,
  assets: LaunchAssetExecutionAssetNodeFragmentFragment[],
) {
  const upstreamAssetKeys = getUpstreamAssetKeys(assets);
  if (upstreamAssetKeys.length === 0) {
    return [];
  }

  const result = await client.query<
    LaunchAssetCheckUpstreamQueryQuery,
    LaunchAssetCheckUpstreamQueryQueryVariables
  >({
    query: LAUNCH_ASSET_CHECK_UPSTREAM_QUERY,
    variables: {assetKeys: upstreamAssetKeys},
  });

  return result.data.assetNodes
    .filter((a) => !a.isSource && a.assetMaterializations.length === 0)
    .map((a) => a.assetKey);
}

export function executionParamsForAssetJob(
  repoAddress: RepoAddress,
  jobName: string,
  assets: {assetKey: AssetKey; opNames: string[]}[],
  tags: {key: string; value: string}[],
): LaunchPipelineExecutionMutationVariables['executionParams'] {
  return {
    mode: 'default',
    executionMetadata: {
      tags: [
        ...tags.map((t) => pick(t, ['key', 'value'])),
        {
          key: DagsterTag.StepSelection,
          value: assets.flatMap((o) => o.opNames).join(','),
        },
      ],
    },
    runConfigData: '{}',
    selector: {
      repositoryLocationName: repoAddress.location,
      repositoryName: repoAddress.name,
      pipelineName: jobName,
      assetSelection: assets.map((asset) => ({
        path: asset.assetKey.path,
      })),
    },
  };
}

export function buildAssetCollisionsAlert(data: LaunchAssetLoaderQueryQuery) {
  return {
    title: MULTIPLE_DEFINITIONS_WARNING,
    body: (
      <div style={{overflow: 'auto'}}>
        One or more of the selected assets are defined in multiple code locations. Rename these
        assets to avoid collisions and then try again.
        <ul>
          {data.assetNodeDefinitionCollisions.map((collision, idx) => (
            <li key={idx}>
              <strong>{displayNameForAssetKey(collision.assetKey)}</strong>
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

export const LAUNCH_ASSET_EXECUTION_ASSET_NODE_FRAGMENT = graphql(`
  fragment LaunchAssetExecutionAssetNodeFragment on AssetNode {
    id
    opNames
    jobNames
    graphName
    partitionDefinition {
      ...PartitionDefinitionForLaunchAsset
    }
    isObservable
    isSource
    assetKey {
      path
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

  fragment PartitionDefinitionForLaunchAsset on PartitionDefinition {
    description
    dimensionTypes {
      name
    }
  }
`);

export const LAUNCH_ASSET_LOADER_QUERY = graphql(`
  query LaunchAssetLoaderQuery($assetKeys: [AssetKeyInput!]!) {
    assetNodes(assetKeys: $assetKeys) {
      id
      ...LaunchAssetExecutionAssetNodeFragment
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
`);

const LAUNCH_ASSET_LOADER_RESOURCE_QUERY = graphql(`
  query LaunchAssetLoaderResourceQuery(
    $pipelineName: String!
    $repositoryLocationName: String!
    $repositoryName: String!
  ) {
    partitionSetsOrError(
      pipelineName: $pipelineName
      repositorySelector: {
        repositoryName: $repositoryName
        repositoryLocationName: $repositoryLocationName
      }
    ) {
      ... on PythonError {
        message
      }
      ... on PipelineNotFoundError {
        message
      }
      ... on PartitionSets {
        results {
          id
          name
        }
      }
    }

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
`);

const LAUNCH_ASSET_CHECK_UPSTREAM_QUERY = graphql(`
  query LaunchAssetCheckUpstreamQuery($assetKeys: [AssetKeyInput!]!) {
    assetNodes(assetKeys: $assetKeys, loadMaterializations: true) {
      id
      assetKey {
        path
      }
      isSource
      opNames
      graphName
      assetMaterializations(limit: 1) {
        runId
      }
    }
  }
`);
