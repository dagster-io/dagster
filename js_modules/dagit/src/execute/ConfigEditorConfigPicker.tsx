import {ApolloClient, gql, useApolloClient, useQuery} from '@apollo/client';
import {
  Button,
  HTMLInputProps,
  Icon,
  IInputGroupProps,
  Intent,
  Menu,
  MenuItem,
} from '@blueprintjs/core';
import {Select, Suggest} from '@blueprintjs/select';
import * as React from 'react';
import * as ReactDOM from 'react-dom';
import styled from 'styled-components';

import {showCustomAlert} from 'src/app/CustomAlertProvider';
import {IExecutionSession} from 'src/app/LocalStorage';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from 'src/app/PythonErrorInfo';
import {ShortcutHandler} from 'src/app/ShortcutHandler';
import {PythonErrorFragment} from 'src/app/types/PythonErrorFragment';
import {ConfigEditorGeneratorPartitionSetsFragment_results} from 'src/execute/types/ConfigEditorGeneratorPartitionSetsFragment';
import {
  ConfigEditorGeneratorPipelineFragment,
  ConfigEditorGeneratorPipelineFragment_presets,
} from 'src/execute/types/ConfigEditorGeneratorPipelineFragment';
import {
  ConfigPartitionsQuery,
  ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results,
} from 'src/execute/types/ConfigPartitionsQuery';
import {RepositorySelector} from 'src/types/globalTypes';
import {Spinner} from 'src/ui/Spinner';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';

type Pipeline = ConfigEditorGeneratorPipelineFragment;
type Preset = ConfigEditorGeneratorPipelineFragment_presets;
type PartitionSet = ConfigEditorGeneratorPartitionSetsFragment_results;
type Partition = ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results;
type ConfigGenerator = Preset | PartitionSet;

interface ConfigEditorConfigPickerProps {
  base: IExecutionSession['base'];
  pipeline: Pipeline;
  partitionSets: PartitionSet[];
  solidSelection: string[] | null;
  onSaveSession: (updates: Partial<IExecutionSession>) => void;
  onCreateSession: (initial: Partial<IExecutionSession>) => void;
  onLoading: () => void;
  onLoaded: () => void;
  repoAddress: RepoAddress;
}

const PRESET_PICKER_HINT_TEXT = `Define a PresetDefinition, PartitionSetDefinition, or a schedule decorator (e.g. @daily_schedule) to autofill this session...`;

class ConfigEditorConfigPickerInternal extends React.Component<
  ConfigEditorConfigPickerProps & {client: ApolloClient<any>}
> {
  onSelectPartitionSet = (partitionSet: PartitionSet) => {
    this.props.onSaveSession({
      base: {
        partitionsSetName: partitionSet.name,
        partitionName: null,
      },
    });
  };

  onSelectPreset = (preset: Preset, pipeline?: Pipeline) => {
    if (!pipeline) {
      console.error('Could not load pipeline tags');
    }

    const tagsDict: {[key: string]: string} = [...(pipeline?.tags || []), ...preset.tags].reduce(
      (tags, kv) => {
        tags[kv.key] = kv.value;
        return tags;
      },
      {},
    );

    this.onCommit({
      base: {presetName: preset.name},
      name: preset.name,
      runConfigYaml: preset.runConfigYaml || '',
      solidSelection: preset.solidSelection,
      solidSelectionQuery: preset.solidSelection === null ? '*' : preset.solidSelection.join(','),
      mode: preset.mode,
      tags: Object.entries(tagsDict).map(([key, value]) => {
        return {key, value};
      }),
    });
  };

  onSelectPartition = async (
    repositorySelector: RepositorySelector,
    partitionSetName: string,
    partitionName: string,
  ) => {
    this.props.onLoading();
    try {
      const {data} = await this.props.client.query({
        query: CONFIG_PARTITION_SELECTION_QUERY,
        variables: {repositorySelector, partitionSetName, partitionName},
      });

      if (
        !data ||
        !data.partitionSetOrError ||
        data.partitionSetOrError.__typename !== 'PartitionSet'
      ) {
        this.props.onLoaded();
        return;
      }

      const {partition} = data.partitionSetOrError;

      let tags;
      if (partition.tagsOrError.__typename === 'PythonError') {
        tags = (this.props.pipeline?.tags || []).slice();
        showCustomAlert({
          body: <PythonErrorInfo error={partition.tagsOrError} />,
        });
      } else {
        tags = [...(this.props.pipeline?.tags || []), ...partition.tagsOrError.results];
      }

      let runConfigYaml;
      if (partition.runConfigOrError.__typename === 'PythonError') {
        runConfigYaml = '';
        showCustomAlert({
          body: <PythonErrorInfo error={partition.runConfigOrError} />,
        });
      } else {
        runConfigYaml = partition.runConfigOrError.yaml;
      }

      this.onCommit({
        name: partition.name,
        base: Object.assign({}, this.props.base, {
          partitionName: partition.name,
        }),
        runConfigYaml,
        solidSelection: partition.solidSelection,
        solidSelectionQuery:
          partition.solidSelection === null ? '*' : partition.solidSelection.join(','),
        mode: partition.mode,
        tags,
      });
    } catch {}
    this.props.onLoaded();
  };

  onCommit = (changes: Partial<IExecutionSession>) => {
    this.props.onSaveSession(changes);
  };

  render() {
    const {pipeline, solidSelection, base, partitionSets, repoAddress} = this.props;

    return (
      <PickerContainer>
        <ConfigEditorConfigGeneratorPicker
          value={base}
          pipeline={pipeline}
          presets={pipeline.presets}
          partitionSets={partitionSets}
          solidSelection={solidSelection}
          onSelectPreset={this.onSelectPreset}
          onSelectPartitionSet={this.onSelectPartitionSet}
        />
        {base && 'partitionsSetName' in base && (
          <>
            <div style={{width: 5}} />
            <ConfigEditorPartitionPicker
              key={base.partitionsSetName}
              pipeline={pipeline}
              partitionSetName={base.partitionsSetName}
              value={base.partitionName}
              onSelect={this.onSelectPartition}
              repoAddress={repoAddress}
            />
          </>
        )}
      </PickerContainer>
    );
  }
}

export const ConfigEditorConfigPicker = (props: ConfigEditorConfigPickerProps) => {
  const client = useApolloClient();
  return <ConfigEditorConfigPickerInternal {...props} client={client} />;
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
      <Button text={undefined} minimal onMouseDown={onClickSort}>
        <Icon icon={sortOrder === 'asc' ? 'sort-alphabetical' : 'sort-alphabetical-desc'} />
      </Button>
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
  pipeline: Pipeline;
  presets: Preset[];
  partitionSets: PartitionSet[];
  solidSelection: string[] | null;
  value: IExecutionSession['base'];
  onSelectPreset: (preset: Preset, pipeline?: Pipeline) => void;
  onSelectPartitionSet: (partitionSet: PartitionSet, pipeline?: Pipeline) => void;
}

const ConfigEditorConfigGeneratorPicker: React.FunctionComponent<ConfigEditorConfigGeneratorPickerProps> = React.memo(
  (props) => {
    const {pipeline, presets, partitionSets, onSelectPreset, onSelectPartitionSet, value} = props;

    const byName = (a: {name: string}, b: {name: string}) => a.name.localeCompare(b.name);

    const configGenerators: ConfigGenerator[] = [...presets, ...partitionSets].sort(byName);

    const empty = configGenerators.length === 0;
    const select: React.RefObject<Select<ConfigGenerator>> = React.createRef();
    const onSelect = (item: ConfigGenerator) => {
      if (item.__typename === 'PartitionSet') {
        onSelectPartitionSet(item, pipeline);
      } else {
        onSelectPreset(item, pipeline);
      }
    };

    let emptyLabel = `Preset / Partition Set`;
    if (presets.length && !partitionSets.length) {
      emptyLabel = `Preset`;
    } else if (!presets.length && partitionSets.length) {
      emptyLabel = `Partition Set`;
    }

    const label = !value
      ? emptyLabel
      : 'presetName' in value
      ? `Preset: ${value.presetName}`
      : `Partition Set: ${value.partitionsSetName}`;

    return (
      <div>
        <ShortcutHandler
          shortcutLabel={'⌥E'}
          shortcutFilter={(e) => e.keyCode === 69 && e.altKey}
          onShortcut={() => activateSelect(select.current)}
        >
          <Select<ConfigGenerator>
            ref={select}
            disabled={empty}
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
                            ? `Solids: ${item.solidSelection[0]}`
                            : `Solids: ${item.solidSelection.length}`
                          : `Solids: All`,
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
            <Button
              disabled={empty}
              text={label}
              title={empty ? PRESET_PICKER_HINT_TEXT : undefined}
              data-test-id="preset-selector-button"
              rightIcon="caret-down"
            />
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

const CONFIG_PARTITION_SELECTION_QUERY = gql`
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
