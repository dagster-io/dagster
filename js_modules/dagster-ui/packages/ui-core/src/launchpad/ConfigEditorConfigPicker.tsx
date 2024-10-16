// eslint-disable-next-line no-restricted-imports
import {HTMLInputProps, InputGroupProps2, Intent} from '@blueprintjs/core';
import {
  Box,
  Button,
  Colors,
  Icon,
  IconWrapper,
  Menu,
  MenuDivider,
  MenuItem,
  Select,
  Spinner,
  Suggest,
} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {gql, useQuery} from '../apollo-client';
import {
  ConfigEditorGeneratorPipelineFragment,
  ConfigEditorPipelinePresetFragment,
  ConfigPartitionsAssetsQuery,
  ConfigPartitionsAssetsQueryVariables,
  ConfigPartitionsQuery,
  ConfigPartitionsQueryVariables,
  PartitionSetForConfigEditorFragment,
} from './types/ConfigEditorConfigPicker.types';
import {AppContext} from '../app/AppContext';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {IExecutionSession} from '../app/ExecutionSessionStorage';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {PartitionDefinitionType, RepositorySelector} from '../graphql/types';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {CreatePartitionDialog} from '../partitions/CreatePartitionDialog';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

type Pipeline = ConfigEditorGeneratorPipelineFragment;
type Preset = ConfigEditorPipelinePresetFragment;
type PartitionSet = PartitionSetForConfigEditorFragment;
type ConfigGenerator = Preset | PartitionSet;

interface ConfigEditorConfigPickerProps {
  base: IExecutionSession['base'];
  pipeline: Pipeline;
  pipelineMode?: string;
  partitionSets: PartitionSet[];
  onSaveSession: (updates: Partial<IExecutionSession>) => void;
  onSelectPreset: (preset: Preset) => Promise<void>;
  onSelectPartition: (
    repositorySelector: RepositorySelector,
    partitionSetName: string,
    partitionName: string,
  ) => Promise<void>;
  repoAddress: RepoAddress;
  assetSelection?: IExecutionSession['assetSelection'];
}

export const ConfigEditorConfigPicker = (props: ConfigEditorConfigPickerProps) => {
  const {
    pipeline,
    base,
    onSaveSession,
    onSelectPreset,
    onSelectPartition,
    partitionSets,
    repoAddress,
    assetSelection,
  } = props;

  const {isJob, presets} = pipeline;

  const configGenerators: ConfigGenerator[] = React.useMemo(() => {
    const byName = (a: {name: string}, b: {name: string}) => a.name.localeCompare(b.name);
    return [...presets, ...partitionSets].sort(byName);
  }, [presets, partitionSets]);

  const label = () => {
    if (!base) {
      if (presets.length && !partitionSets.length) {
        return 'Preset';
      }
      if (!presets.length && partitionSets.length) {
        return 'Partition Set';
      }
      return 'Preset / Partition Set';
    }

    if ('presetName' in base) {
      return `Preset: ${base.presetName}`;
    }
    if ('partitionsSetName' in base) {
      return `Partition Set: ${base.partitionsSetName}`;
    }
    return `Partitions`;
  };

  const onSelect = (item: ConfigGenerator) => {
    if (item.__typename === 'PartitionSet') {
      onSaveSession({
        mode: item.mode,
        base: {
          type: 'op-job-partition-set',
          partitionsSetName: item.name,
          partitionName: null,
          tags: base ? base.tags : null,
        },
      });
    } else {
      onSelectPreset(item);
    }
  };

  return (
    <PickerContainer>
      {isJob || configGenerators.length < 1 ? null : (
        <ConfigEditorConfigGeneratorPicker
          label={label()}
          configGenerators={configGenerators}
          onSelect={onSelect}
        />
      )}
      {base && 'partitionName' in base ? (
        <ConfigEditorPartitionPicker
          pipeline={pipeline}
          partitionSetName={'partitionsSetName' in base ? base.partitionsSetName : ''}
          value={base.partitionName}
          onSelect={onSelectPartition}
          repoAddress={repoAddress}
          assetSelection={assetSelection}
        />
      ) : null}
    </PickerContainer>
  );
};

interface ConfigEditorPartitionPickerProps {
  pipeline: Pipeline;
  partitionSetName: string;
  value: string | null;
  onSelect: (
    repositorySelector: RepositorySelector,
    partitionSetName: string,
    partitionName: string,
  ) => void;
  repoAddress: RepoAddress;
  assetSelection?: IExecutionSession['assetSelection'];
}

const SORT_ORDER_KEY_BASE = 'dagster.partition-sort-order';
type SortOrder = 'asc' | 'desc';

const ConfigEditorPartitionPicker = React.memo((props: ConfigEditorPartitionPickerProps) => {
  const {partitionSetName, value, onSelect, repoAddress, assetSelection} = props;
  const {basePath} = React.useContext(AppContext);
  const repositorySelector = repoAddressToSelector(repoAddress);

  const queryResultNoAssets = useQuery<ConfigPartitionsQuery, ConfigPartitionsQueryVariables>(
    CONFIG_PARTITIONS_QUERY,
    {
      skip: !!assetSelection,
      variables: {repositorySelector, partitionSetName},
      fetchPolicy: 'network-only',
    },
  );

  const queryResultAssets = useQuery<
    ConfigPartitionsAssetsQuery,
    ConfigPartitionsAssetsQueryVariables
  >(CONFIG_PARTITIONS_ASSETS_QUERY, {
    skip: !assetSelection,
    variables: {
      params: {
        ...repositorySelector,
        pipelineName: props.pipeline.name,
      },
      assetKeys: assetSelection
        ? assetSelection.map((selection) => ({path: selection.assetKey.path}))
        : [],
    },
    fetchPolicy: 'network-only',
  });

  const queryResult = assetSelection ? queryResultAssets : queryResultNoAssets;
  const {data, refetch, loading} = queryResult;

  const sortOrderKey = `${SORT_ORDER_KEY_BASE}-${basePath}-${repoAddressAsHumanString(
    repoAddress,
  )}-${partitionSetName}`;

  const [sortOrder, setSortOrder] = useStateWithStorage<SortOrder>(sortOrderKey, (value: any) =>
    value === undefined ? 'asc' : value,
  );

  const doesAnyAssetHavePartitions = React.useMemo(
    () =>
      data && 'assetNodes' in data && data.assetNodes?.some((node) => !!node.partitionDefinition),
    [data],
  );

  const partitions: string[] = React.useMemo(() => {
    const retrieved = partitionKeysFromData(data);
    return sortOrder === 'asc' ? retrieved : [...retrieved].reverse();
  }, [data, sortOrder]);

  const error = errorFromData(data);
  const selected = value && partitions.includes(value) ? value : undefined;

  const onClickSort = React.useCallback(
    (event: React.MouseEvent<HTMLButtonElement>) => {
      event.preventDefault();
      setSortOrder((order) => (order === 'asc' ? 'desc' : 'asc'));
    },
    [setSortOrder],
  );

  const rightElement = partitions.length ? (
    <SortButton onMouseDown={onClickSort}>
      <Icon name="sort_by_alpha" color={Colors.accentGray()} />
    </SortButton>
  ) : undefined;

  const inputProps: InputGroupProps2 & HTMLInputProps = {
    placeholder: 'Partition',
    style: {width: 180},
    intent: (loading ? !!value : !!selected) ? Intent.NONE : Intent.DANGER,
    rightElement,
  };

  const {isDynamicPartition, dynamicPartitionsDefinitionName} = React.useMemo(() => {
    const assetNodes = data && 'assetNodes' in data ? data?.assetNodes : undefined;
    const definition = assetNodes?.find((a) => !!a.partitionDefinition)?.partitionDefinition;
    if (
      !definition ||
      assetNodes?.some(
        (node) =>
          node?.partitionDefinition?.name && node?.partitionDefinition?.name !== definition?.name,
      )
    ) {
      return {isDynamicPartition: false, dynamicPartitionsDefinitionName: undefined};
    }
    return {
      isDynamicPartition: definition.type === PartitionDefinitionType.DYNAMIC,
      dynamicPartitionsDefinitionName: definition.name,
    };
  }, [data]);

  const [showCreatePartition, setShowCreatePartition] = React.useState(false);

  // If we are loading the partitions and do NOT have any cached data to display,
  // show the component in a loading state with a spinner and fill it with the
  // current partition's name so it doesn't flicker (if one is set already.)
  if (loading && partitions.length === 0) {
    return (
      <Suggest<string>
        key="loading"
        inputProps={{
          ...inputProps,
          rightElement: !value ? (
            <Box
              flex={{direction: 'column', justifyContent: 'center'}}
              padding={{right: 4}}
              style={{height: '30px'}}
            >
              <Spinner purpose="body-text" />
            </Box>
          ) : undefined,
        }}
        items={[]}
        itemRenderer={() => null}
        noResults={<MenuItem disabled={true} text="Loading..." />}
        inputValueRenderer={(str) => str}
        selectedItem={value}
        onItemSelect={() => {}}
      />
    );
  }

  if (error) {
    showCustomAlert({
      body: <PythonErrorInfo error={error} />,
    });
  }

  if (assetSelection?.length && !doesAnyAssetHavePartitions) {
    return null;
  }

  // Note: We don't want this Suggest to be a fully "controlled" React component.
  // Keeping it's state is annoyign and we only want to update our data model on
  // selection change. However, we need to set an initial value (defaultSelectedItem)
  // and ensure it is re-applied to the internal state when it changes (via `key` below).
  return (
    <>
      <Suggest<string>
        key={selected ? selected : 'none'}
        defaultSelectedItem={selected}
        items={partitions}
        inputProps={inputProps}
        inputValueRenderer={(partition) => partition}
        itemPredicate={(query, partition) => {
          const sanitized = query.trim().toLocaleLowerCase();
          return sanitized.length === 0 || partition.toLocaleLowerCase().includes(sanitized);
        }}
        itemRenderer={(partition, props) => (
          <MenuItem
            active={props.modifiers.active}
            onClick={props.handleClick}
            key={partition}
            text={partition}
          />
        )}
        noResults={<MenuItem disabled={true} text="No presets." />}
        onItemSelect={(item) => {
          onSelect(repositorySelector, partitionSetName, item);
        }}
      />
      {isDynamicPartition ? (
        <Button
          onClick={() => {
            setShowCreatePartition(true);
          }}
        >
          Add new partition
        </Button>
      ) : null}
      {/* Wrapper div to avoid any key conflicts with the key on the Suggestion component */}
      <div>
        <CreatePartitionDialog
          key={showCreatePartition ? '1' : '0'}
          isOpen={showCreatePartition}
          dynamicPartitionsDefinitionName={dynamicPartitionsDefinitionName}
          repoAddress={repoAddress}
          close={() => {
            setShowCreatePartition(false);
          }}
          refetch={async () => {
            await refetch();
          }}
          onCreated={(partitionName) => {
            onSelect(repositorySelector, partitionSetName, partitionName);
          }}
        />
      </div>
    </>
  );
});

interface ConfigEditorConfigGeneratorPickerProps {
  label: string;
  configGenerators: ConfigGenerator[];
  onSelect: (configGenerator: ConfigGenerator) => void;
}

const ConfigEditorConfigGeneratorPicker = React.memo(
  (props: ConfigEditorConfigGeneratorPickerProps) => {
    const {configGenerators, label, onSelect} = props;
    const button = React.useRef<HTMLButtonElement>(null);

    return (
      <div>
        <ShortcutHandler
          shortcutLabel="⌥E"
          shortcutFilter={(e) => e.code === 'KeyE' && e.altKey}
          onShortcut={() => button.current?.click()}
        >
          <Select<ConfigGenerator>
            items={configGenerators}
            itemPredicate={(query, configGenerator) =>
              query.length === 0 || configGenerator.name.includes(query)
            }
            itemListRenderer={({itemsParentRef, renderItem, filteredItems}) => {
              const renderedPresetItems = filteredItems
                .filter((item) => item.__typename === 'PipelinePreset')
                .map(renderItem)
                .filter(Boolean);

              const renderedPartitionSetItems = filteredItems
                .filter((item) => item.__typename === 'PartitionSet')
                .map(renderItem)
                .filter(Boolean);

              const bothTypesPresent =
                renderedPresetItems.length > 0 && renderedPartitionSetItems.length > 0;

              return (
                <Menu ulRef={itemsParentRef}>
                  {bothTypesPresent && <MenuItem disabled={true} text="Presets" />}
                  {renderedPresetItems}
                  {bothTypesPresent && <MenuDivider />}
                  {bothTypesPresent && <MenuItem disabled={true} text="Partition Sets" />}
                  {renderedPartitionSetItems}
                </Menu>
              );
            }}
            itemRenderer={(item, props) => (
              <MenuItem
                active={props.modifiers.active}
                onClick={props.handleClick}
                key={item.name}
                text={
                  <div>
                    {item.name}
                    <div style={{opacity: 0.4, fontSize: '0.75rem'}}>
                      {[
                        item.solidSelection
                          ? item.solidSelection.length === 1
                            ? `Ops: ${item.solidSelection[0]}`
                            : `Ops: ${item.solidSelection.length}`
                          : `Ops: All`,
                        `Mode: ${item.mode}`,
                      ].join(' - ')}
                    </div>
                  </div>
                }
              />
            )}
            noResults={<MenuItem disabled={true} text="No presets." />}
            onItemSelect={onSelect}
          >
            <Button
              ref={button}
              data-test-id="preset-selector-button"
              rightIcon={<Icon name="expand_more" />}
            >
              {label}
            </Button>
          </Select>
        </ShortcutHandler>
      </div>
    );
  },
);

export const SortButton = styled.button`
  border: 0;
  cursor: pointer;
  padding: 4px;
  margin: 3px 3px 0 0;
  background-color: ${Colors.backgroundLighter()};
  border-radius: 4px;
  transition: background-color 100ms;

  :focus {
    background-color: ${Colors.backgroundLighterHover()};
    outline: none;
  }
  :hover {
    ${IconWrapper} {
      background-color: ${Colors.backgroundLight()};
    }
  }
`;

const PickerContainer = styled.div`
  display: flex;
  justify: space-between;
  align-items: center;
  gap: 6px;
`;

const CONFIG_PARTITIONS_QUERY = gql`
  query ConfigPartitionsQuery(
    $repositorySelector: RepositorySelector!
    $partitionSetName: String!
  ) {
    partitionSetOrError(
      repositorySelector: $repositorySelector
      partitionSetName: $partitionSetName
    ) {
      ... on PartitionSet {
        id
        partitionsOrError {
          ... on Partitions {
            results {
              ...ConfigPartitionResult
            }
          }
          ...PythonErrorFragment
        }
      }
    }
  }

  fragment ConfigPartitionResult on Partition {
    name
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

const CONFIG_PARTITIONS_ASSETS_QUERY = gql`
  query ConfigPartitionsAssetsQuery($params: PipelineSelector!, $assetKeys: [AssetKeyInput!]) {
    pipelineOrError(params: $params) {
      ...PythonErrorFragment
      ... on PipelineNotFoundError {
        message
      }
      ... on InvalidSubsetError {
        message
      }
      ... on Pipeline {
        id
        partitionKeysOrError(selectedAssetKeys: $assetKeys) {
          ... on PartitionKeys {
            partitionKeys
          }
        }
      }
    }
    assetNodes(assetKeys: $assetKeys) {
      id
      partitionDefinition {
        name
        type
      }
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

export const CONFIG_EDITOR_GENERATOR_PIPELINE_FRAGMENT = gql`
  fragment ConfigEditorGeneratorPipelineFragment on Pipeline {
    id
    isJob
    name
    presets {
      ...ConfigEditorPipelinePreset
    }
    tags {
      key
      value
    }
  }

  fragment ConfigEditorPipelinePreset on PipelinePreset {
    name
    mode
    solidSelection
    runConfigYaml
    tags {
      key
      value
    }
  }
`;

export const CONFIG_EDITOR_GENERATOR_PARTITION_SETS_FRAGMENT = gql`
  fragment ConfigEditorGeneratorPartitionSetsFragment on PartitionSets {
    results {
      id
      ...PartitionSetForConfigEditor
    }
  }

  fragment PartitionSetForConfigEditor on PartitionSet {
    id
    name
    mode
    solidSelection
  }
`;

function partitionKeysFromData(
  data: ConfigPartitionsAssetsQuery | ConfigPartitionsQuery | undefined,
) {
  if (!data) {
    return [];
  }

  if (
    'partitionSetOrError' in data &&
    data.partitionSetOrError.__typename === 'PartitionSet' &&
    data.partitionSetOrError.partitionsOrError.__typename === 'Partitions'
  ) {
    return data.partitionSetOrError.partitionsOrError.results.map((a) => a.name);
  }
  if ('pipelineOrError' in data && data.pipelineOrError.__typename === 'Pipeline') {
    return data.pipelineOrError.partitionKeysOrError.partitionKeys;
  }
  return [];
}

function errorFromData(data: ConfigPartitionsAssetsQuery | ConfigPartitionsQuery | undefined) {
  if (!data) {
    return null;
  }
  if (
    'partitionSetOrError' in data &&
    data.partitionSetOrError.__typename === 'PartitionSet' &&
    data.partitionSetOrError.partitionsOrError.__typename !== 'Partitions'
  ) {
    return data.partitionSetOrError.partitionsOrError;
  }
  if (
    'pipelineOrError' in data &&
    data.pipelineOrError &&
    data.pipelineOrError.__typename !== 'Pipeline'
  ) {
    return data.pipelineOrError;
  }
  return null;
}
