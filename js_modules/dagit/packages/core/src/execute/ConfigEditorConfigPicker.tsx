import {gql, useQuery} from '@apollo/client';
import {Button, HTMLInputProps, IInputGroupProps, Intent, Menu, MenuItem} from '@blueprintjs/core';
import {Select, Suggest} from '@blueprintjs/select';
import * as React from 'react';
import * as ReactDOM from 'react-dom';
import styled from 'styled-components/macro';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {useFeatureFlags} from '../app/Flags';
import {IExecutionSession} from '../app/LocalStorage';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment';
import {RepositorySelector} from '../types/globalTypes';
import {ColorsWIP} from '../ui/Colors';
import {IconWIP} from '../ui/Icon';
import {Spinner} from '../ui/Spinner';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {ConfigEditorGeneratorPartitionSetsFragment_results} from './types/ConfigEditorGeneratorPartitionSetsFragment';
import {
  ConfigEditorGeneratorPipelineFragment,
  ConfigEditorGeneratorPipelineFragment_presets,
} from './types/ConfigEditorGeneratorPipelineFragment';
import {
  ConfigPartitionsQuery,
  ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results,
} from './types/ConfigPartitionsQuery';

type Pipeline = ConfigEditorGeneratorPipelineFragment;
type Preset = ConfigEditorGeneratorPipelineFragment_presets;
type PartitionSet = ConfigEditorGeneratorPartitionSetsFragment_results;
type Partition = ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results;
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
}

export const ConfigEditorConfigPicker: React.FC<ConfigEditorConfigPickerProps> = (props) => {
  const {
    pipeline,
    pipelineMode,
    base,
    onSaveSession,
    onSelectPreset,
    onSelectPartition,
    partitionSets,
    repoAddress,
  } = props;

  const {presets} = pipeline;

  const configGenerators: ConfigGenerator[] = React.useMemo(() => {
    const byName = (a: {name: string}, b: {name: string}) => a.name.localeCompare(b.name);
    return [...presets, ...partitionSets]
      .filter(({mode}) => !pipelineMode || mode === pipelineMode)
      .sort(byName);
  }, [presets, partitionSets, pipelineMode]);

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

    return `Partition Set: ${base.partitionsSetName}`;
  };

  const onSelect = (item: ConfigGenerator) => {
    if (item.__typename === 'PartitionSet') {
      onSaveSession({
        mode: item.mode,
        base: {
          partitionsSetName: item.name,
          partitionName: null,
        },
      });
    } else {
      onSelectPreset(item);
    }
  };

  return (
    <PickerContainer>
      {pipelineMode && configGenerators.length <= 1 ? null : (
        <ConfigEditorConfigGeneratorPicker
          label={label()}
          configGenerators={configGenerators}
          onSelect={onSelect}
        />
      )}
      {base && 'partitionsSetName' in base ? (
        <ConfigEditorPartitionPicker
          pipeline={pipeline}
          partitionSetName={base.partitionsSetName}
          value={base.partitionName}
          onSelect={onSelectPartition}
          repoAddress={repoAddress}
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
}

const ConfigEditorPartitionPicker: React.FC<ConfigEditorPartitionPickerProps> = React.memo(
  (props) => {
    const {partitionSetName, value, onSelect, repoAddress} = props;
    const repositorySelector = repoAddressToSelector(repoAddress);
    const {data, loading} = useQuery<ConfigPartitionsQuery>(CONFIG_PARTITIONS_QUERY, {
      variables: {repositorySelector, partitionSetName},
      fetchPolicy: 'network-only',
    });

    const [sortOrder, setSortOrder] = React.useState('asc');

    const partitions: Partition[] = React.useMemo(() => {
      const retrieved =
        data?.partitionSetOrError.__typename === 'PartitionSet' &&
        data?.partitionSetOrError.partitionsOrError.__typename === 'Partitions'
          ? data.partitionSetOrError.partitionsOrError.results
          : [];
      return sortOrder === 'asc' ? retrieved : [...retrieved].reverse();
    }, [data, sortOrder]);

    const error: PythonErrorFragment | null =
      data?.partitionSetOrError.__typename === 'PartitionSet' &&
      data?.partitionSetOrError.partitionsOrError.__typename !== 'Partitions'
        ? data.partitionSetOrError.partitionsOrError
        : null;

    const selected = partitions.find((p) => p.name === value);

    const onClickSort = React.useCallback((event) => {
      event.preventDefault();
      setSortOrder((order) => (order === 'asc' ? 'desc' : 'asc'));
    }, []);

    const rightElement = partitions.length ? (
      <Button
        icon={<IconWIP name="sort_by_alpha" color={ColorsWIP.Gray400} />}
        minimal
        onMouseDown={onClickSort}
      ></Button>
    ) : undefined;

    const inputProps: IInputGroupProps & HTMLInputProps = {
      placeholder: 'Partition',
      style: {width: 180},
      intent: (loading ? !!value : !!selected) ? Intent.NONE : Intent.DANGER,
      rightElement,
    };

    // If we are loading the partitions and do NOT have any cached data to display,
    // show the component in a loading state with a spinner and fill it with the
    // current partition's name so it doesn't flicker (if one is set already.)
    if (loading && partitions.length === 0) {
      return (
        <Suggest<string>
          key="loading"
          inputProps={{
            ...inputProps,
            rightElement: !value ? <Spinner purpose="body-text" /> : undefined,
          }}
          items={[]}
          itemRenderer={() => null}
          noResults={<Menu.Item disabled={true} text="Loading..." />}
          inputValueRenderer={(str) => str}
          selectedItem={value}
        />
      );
    }

    if (error) {
      showCustomAlert({
        body: <PythonErrorInfo error={error} />,
      });
    }

    // Note: We don't want this Suggest to be a fully "controlled" React component.
    // Keeping it's state is annoyign and we only want to update our data model on
    // selection change. However, we need to set an initial value (defaultSelectedItem)
    // and ensure it is re-applied to the internal state when it changes (via `key` below).
    return (
      <Suggest<Partition>
        key={selected ? selected.name : 'none'}
        defaultSelectedItem={selected}
        items={partitions}
        inputProps={inputProps}
        inputValueRenderer={(partition) => partition.name}
        itemPredicate={(query, partition) => query.length === 0 || partition.name.includes(query)}
        itemRenderer={(partition, props) => (
          <Menu.Item
            active={props.modifiers.active}
            onClick={props.handleClick}
            key={partition.name}
            text={partition.name}
          />
        )}
        noResults={<Menu.Item disabled={true} text="No presets." />}
        onItemSelect={(item) => {
          onSelect(repositorySelector, partitionSetName, item.name);
        }}
      />
    );
  },
);

interface ConfigEditorConfigGeneratorPickerProps {
  label: string;
  configGenerators: ConfigGenerator[];
  onSelect: (configGenerator: ConfigGenerator) => void;
}

const ConfigEditorConfigGeneratorPicker: React.FC<ConfigEditorConfigGeneratorPickerProps> = React.memo(
  (props) => {
    const {configGenerators, label, onSelect} = props;
    const {flagPipelineModeTuples} = useFeatureFlags();
    const select = React.useRef<Select<ConfigGenerator>>(null);
    const itemLabel = flagPipelineModeTuples ? 'Ops' : 'Solids';

    return (
      <div>
        <ShortcutHandler
          shortcutLabel={'⌥E'}
          shortcutFilter={(e) => e.keyCode === 69 && e.altKey}
          onShortcut={() => activateSelect(select.current)}
        >
          <Select<ConfigGenerator>
            ref={select}
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
                  {bothTypesPresent && <MenuItem disabled={true} text={`Presets`} />}
                  {renderedPresetItems}
                  {bothTypesPresent && <Menu.Divider />}
                  {bothTypesPresent && <MenuItem disabled={true} text={`Partition Sets`} />}
                  {renderedPartitionSetItems}
                </Menu>
              );
            }}
            itemRenderer={(item, props) => (
              <Menu.Item
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
                            ? `${itemLabel}: ${item.solidSelection[0]}`
                            : `${itemLabel}: ${item.solidSelection.length}`
                          : `${itemLabel}: All`,
                        `Mode: ${item.mode}`,
                      ].join(' - ')}
                    </div>
                  </div>
                }
              />
            )}
            noResults={<Menu.Item disabled={true} text="No presets." />}
            onItemSelect={onSelect}
          >
            <Button text={label} data-test-id="preset-selector-button" rightIcon="caret-down" />
          </Select>
        </ShortcutHandler>
      </div>
    );
  },
);

function activateSelect(select: Select<any> | null) {
  if (!select) {
    return;
  }
  // eslint-disable-next-line react/no-find-dom-node
  const selectEl = ReactDOM.findDOMNode(select) as HTMLElement;
  const btnEl = selectEl.querySelector('button');
  if (btnEl) {
    btnEl.click();
  }
}

const PickerContainer = styled.div`
  display: flex;
  justify: space-between;
  align-items: center;
`;

export const CONFIG_EDITOR_GENERATOR_PIPELINE_FRAGMENT = gql`
  fragment ConfigEditorGeneratorPipelineFragment on Pipeline {
    id
    name
    presets {
      __typename
      name
      mode
      solidSelection
      runConfigYaml
      tags {
        key
        value
      }
    }
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
      name
      mode
      solidSelection
    }
  }
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
      __typename
      ... on PartitionSet {
        id
        partitionsOrError {
          ... on Partitions {
            results {
              name
            }
          }
          ... on PythonError {
            ...PythonErrorFragment
          }
        }
      }
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;

export const CONFIG_PARTITION_SELECTION_QUERY = gql`
  query ConfigPartitionSelectionQuery(
    $repositorySelector: RepositorySelector!
    $partitionSetName: String!
    $partitionName: String!
  ) {
    partitionSetOrError(
      repositorySelector: $repositorySelector
      partitionSetName: $partitionSetName
    ) {
      __typename
      ... on PartitionSet {
        id
        partition(partitionName: $partitionName) {
          name
          solidSelection
          runConfigOrError {
            ... on PartitionRunConfig {
              yaml
            }
            ... on PythonError {
              ...PythonErrorFragment
            }
          }
          mode
          tagsOrError {
            ... on PartitionTags {
              results {
                key
                value
              }
            }
            ... on PythonError {
              ...PythonErrorFragment
            }
          }
        }
      }
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
