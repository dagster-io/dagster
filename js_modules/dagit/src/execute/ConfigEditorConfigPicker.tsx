import * as React from "react";
import {
  Button,
  Menu,
  Spinner,
  MenuItem,
  Intent,
  IInputGroupProps,
  HTMLInputProps
} from "@blueprintjs/core";
import * as ReactDOM from "react-dom";

import { Select, Suggest } from "@blueprintjs/select";
import { useQuery, withApollo, WithApolloClient } from "react-apollo";
import {
  ConfigPresetsQuery,
  ConfigPresetsQuery_pipelineOrError_Pipeline_presets
} from "./types/ConfigPresetsQuery";
import {
  ConfigPartitionsQuery,
  ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitions_results
} from "./types/ConfigPartitionsQuery";
import {
  ConfigPartitionSetsQuery,
  ConfigPartitionSetsQuery_partitionSetsOrError_PartitionSets_results
} from "./types/ConfigPartitionSetsQuery";
import gql from "graphql-tag";
import { IExecutionSession } from "../LocalStorage";
import { isEqual } from "apollo-utilities";
import styled from "styled-components";
import { ShortcutHandler } from "../ShortcutHandler";
import {
  useRepositorySelector,
  usePipelineSelector
} from "../DagsterRepositoryContext";

type Preset = ConfigPresetsQuery_pipelineOrError_Pipeline_presets;
type PartitionSet = ConfigPartitionSetsQuery_partitionSetsOrError_PartitionSets_results;
type Partition = ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitions_results;
type ConfigGenerator = Preset | PartitionSet;
interface Pipeline {
  tags: {
    key: string;
    value: string;
  }[];
}

interface ConfigEditorConfigPickerProps {
  base: IExecutionSession["base"];
  pipelineName: string;
  solidSelection: string[] | null;
  onSaveSession: (updates: Partial<IExecutionSession>) => void;
  onCreateSession: (initial: Partial<IExecutionSession>) => void;
  onLoading: () => void;
  onLoaded: () => void;
}

const PRESET_PICKER_HINT_TEXT = `Define a PresetDefinition, PartitionSetDefinition, or a schedule decorator (e.g. @daily_schedule) to autofill this session...`;

class ConfigEditorConfigPickerInternal extends React.Component<
  WithApolloClient<ConfigEditorConfigPickerProps>
> {
  onSelectPartitionSet = (partitionSet: PartitionSet) => {
    this.props.onSaveSession({
      base: {
        partitionsSetName: partitionSet.name,
        partitionName: null
      }
    });
  };

  onSelectPreset = (preset: Preset, pipeline?: Pipeline) => {
    if (!pipeline) {
      console.error("Could not load pipeline tags");
    }
    this.onCommit({
      base: { presetName: preset.name },
      name: preset.name,
      runConfigYaml: preset.runConfigYaml || "",
      solidSelection: preset.solidSelection,
      solidSelectionQuery:
        preset.solidSelection === null ? "*" : preset.solidSelection.join(","),
      mode: preset.mode,
      tags: [...(pipeline?.tags || [])]
    });
  };

  onSelectPartition = async (
    partitionSetName: string,
    partitionName: string,
    pipeline?: Pipeline
  ) => {
    if (!pipeline) {
      console.error("Could not load pipeline tags");
    }

    this.props.onLoading();
    try {
      const { data } = await this.props.client.query({
        query: CONFIG_PARTITION_SELECTION_QUERY,
        variables: { partitionSetName, partitionName }
      });

      if (
        !data ||
        !data.partitionSetOrError ||
        data.partitionSetOrError.__typename !== "PartitionSet"
      ) {
        this.props.onLoaded();
        return;
      }

      const { partition } = data.partitionSetOrError;

      this.onCommit({
        name: partition.name,
        base: Object.assign({}, this.props.base, {
          partitionName: partition.name
        }),
        runConfigYaml: partition.runConfigYaml || "",
        solidSelection: partition.solidSelection,
        solidSelectionQuery:
          partition.solidSelection === null
            ? "*"
            : partition.solidSelection.join(","),
        mode: partition.mode,
        tags: [...(pipeline?.tags || []), ...partition.tags]
      });
    } catch {}
    this.props.onLoaded();
  };

  onCommit = (changes: Partial<IExecutionSession>) => {
    this.props.onSaveSession(changes);
  };

  render() {
    const { pipelineName, solidSelection, base } = this.props;

    return (
      <PickerContainer>
        <ConfigEditorConfigGeneratorPicker
          value={base}
          pipelineName={pipelineName}
          solidSelection={solidSelection}
          onSelectPreset={this.onSelectPreset}
          onSelectPartitionSet={this.onSelectPartitionSet}
        />
        {base && "partitionsSetName" in base && (
          <>
            <div style={{ width: 5 }} />
            <ConfigEditorPartitionPicker
              key={base.partitionsSetName}
              pipelineName={pipelineName}
              partitionSetName={base.partitionsSetName}
              value={base.partitionName}
              onSelect={this.onSelectPartition}
            />
          </>
        )}
      </PickerContainer>
    );
  }
}

export const ConfigEditorConfigPicker = withApollo<
  ConfigEditorConfigPickerProps
>(ConfigEditorConfigPickerInternal);

interface ConfigEditorPartitionPickerProps {
  pipelineName: string;
  partitionSetName: string;
  value: string | null;
  onSelect: (
    partitionSetName: string,
    partitionName: string,
    pipeline?: Pipeline
  ) => void;
}

export const ConfigEditorPartitionPicker: React.FunctionComponent<ConfigEditorPartitionPickerProps> = React.memo(
  props => {
    const { partitionSetName, pipelineName, value, onSelect } = props;
    const pipelineSelector = usePipelineSelector(pipelineName);
    const { data, loading } = useQuery<ConfigPartitionsQuery>(
      CONFIG_PARTITIONS_QUERY,
      {
        variables: { partitionSetName, pipelineSelector },
        fetchPolicy: "network-only"
      }
    );

    const partitions: Partition[] =
      data?.partitionSetOrError.__typename === "PartitionSet"
        ? data.partitionSetOrError.partitions.results
        : [];

    const pipeline: Pipeline | undefined =
      data?.pipelineOrError.__typename === "Pipeline"
        ? data.pipelineOrError
        : undefined;
    const selected = partitions.find(p => p.name === value);

    const inputProps: IInputGroupProps & HTMLInputProps = {
      placeholder: "Partition",
      style: { width: 180 },
      intent: (loading ? !!value : !!selected) ? Intent.NONE : Intent.DANGER
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
            rightElement: !value ? <Spinner size={17} /> : undefined
          }}
          items={[]}
          itemRenderer={() => null}
          noResults={<Menu.Item disabled={true} text="Loading..." />}
          inputValueRenderer={str => str}
          selectedItem={value}
        />
      );
    }

    // Note: We don't want this Suggest to be a fully "controlled" React component.
    // Keeping it's state is annoyign and we only want to update our data model on
    // selection change. However, we need to set an initial value (defaultSelectedItem)
    // and ensure it is re-applied to the internal state when it changes (via `key` below).
    return (
      <Suggest<Partition>
        key={selected ? selected.name : "none"}
        defaultSelectedItem={selected}
        items={partitions}
        inputProps={inputProps}
        inputValueRenderer={partition => partition.name}
        itemPredicate={(query, partition) =>
          query.length === 0 || partition.name.includes(query)
        }
        itemRenderer={(partition, props) => (
          <Menu.Item
            active={props.modifiers.active}
            onClick={props.handleClick}
            key={partition.name}
            text={partition.name}
          />
        )}
        noResults={<Menu.Item disabled={true} text="No presets." />}
        onItemSelect={item => {
          return onSelect(partitionSetName, item.name, pipeline);
        }}
      />
    );
  },
  isEqual
);

interface ConfigEditorConfigGeneratorPickerProps {
  pipelineName: string;
  solidSelection: string[] | null;
  value: IExecutionSession["base"];
  onSelectPreset: (preset: Preset, pipeline?: Pipeline) => void;
  onSelectPartitionSet: (
    partitionSet: PartitionSet,
    pipeline?: Pipeline
  ) => void;
}

export const ConfigEditorConfigGeneratorPicker: React.FunctionComponent<ConfigEditorConfigGeneratorPickerProps> = React.memo(
  props => {
    const { pipelineName, onSelectPreset, onSelectPartitionSet, value } = props;
    const {
      presets,
      partitionSets,
      loading,
      pipeline
    } = usePresetsAndPartitions(pipelineName);

    const configGenerators: ConfigGenerator[] = [...presets, ...partitionSets];
    const empty = !loading && configGenerators.length === 0;

    const select: React.RefObject<Select<ConfigGenerator>> = React.createRef();
    const onSelect = (item: ConfigGenerator) => {
      if (item.__typename === "PartitionSet") {
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
      : "presetName" in value
      ? `Preset: ${value.presetName}`
      : `Partition Set: ${value.partitionsSetName}`;

    return (
      <div>
        <ShortcutHandler
          shortcutLabel={"⌥E"}
          shortcutFilter={e => e.keyCode === 69 && e.altKey}
          onShortcut={() => activateSelect(select.current)}
        >
          <Select<ConfigGenerator>
            ref={select}
            disabled={empty}
            items={configGenerators}
            itemPredicate={(query, configGenerator) =>
              query.length === 0 || configGenerator.name.includes(query)
            }
            itemListRenderer={({
              itemsParentRef,
              renderItem,
              filteredItems
            }) => {
              const renderedPresetItems = filteredItems
                .filter(item => item.__typename === "PipelinePreset")
                .map(renderItem)
                .filter(Boolean);

              const renderedPartitionSetItems = filteredItems
                .filter(item => item.__typename === "PartitionSet")
                .map(renderItem)
                .filter(Boolean);

              const bothTypesPresent =
                renderedPresetItems.length > 0 &&
                renderedPartitionSetItems.length > 0;

              return (
                <Menu ulRef={itemsParentRef}>
                  {bothTypesPresent && (
                    <MenuItem disabled={true} text={`Presets`} />
                  )}
                  {renderedPresetItems}
                  {bothTypesPresent && <Menu.Divider />}
                  {bothTypesPresent && (
                    <MenuItem disabled={true} text={`Partition Sets`} />
                  )}
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
                    <div style={{ opacity: 0.4, fontSize: "0.75rem" }}>
                      {[
                        item.solidSelection
                          ? item.solidSelection.length === 1
                            ? `Solids: ${item.solidSelection[0]}`
                            : `Solids: ${item.solidSelection.length}`
                          : `Solids: All`,
                        `Mode: ${item.mode}`
                      ].join(" - ")}
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
  isEqual
);

function activateSelect(select: Select<any> | null) {
  if (!select) return;
  // eslint-disable-next-line react/no-find-dom-node
  const selectEl = ReactDOM.findDOMNode(select) as HTMLElement;
  const btnEl = selectEl.querySelector("button");
  if (btnEl) {
    btnEl.click();
  }
}

const PickerContainer = styled.div`
  display: flex;
  justify: space-between;
  align-items: center;
`;

const CONFIG_PRESETS_QUERY = gql`
  query ConfigPresetsQuery($pipelineSelector: PipelineSelector!) {
    pipelineOrError(params: $pipelineSelector) {
      __typename
      ... on Pipeline {
        name
        presets {
          __typename
          name
          mode
          solidSelection
          runConfigYaml
        }
        tags {
          key
          value
        }
      }
    }
  }
`;

export const CONFIG_PARTITION_SETS_QUERY = gql`
  query ConfigPartitionSetsQuery(
    $repositorySelector: RepositorySelector!
    $pipelineName: String!
  ) {
    partitionSetsOrError(
      repositorySelector: $repositorySelector
      pipelineName: $pipelineName
    ) {
      __typename
      ... on PartitionSets {
        results {
          name
          mode
          solidSelection
        }
      }
    }
  }
`;

const CONFIG_PARTITIONS_QUERY = gql`
  query ConfigPartitionsQuery(
    $partitionSetName: String!
    $pipelineSelector: PipelineSelector!
  ) {
    pipelineOrError(params: $pipelineSelector) {
      __typename
      ... on Pipeline {
        name
        tags {
          key
          value
        }
      }
    }
    partitionSetOrError(partitionSetName: $partitionSetName) {
      __typename
      ... on PartitionSet {
        partitions {
          results {
            name
          }
        }
      }
    }
  }
`;

const CONFIG_PARTITION_SELECTION_QUERY = gql`
  query ConfigPartitionSelectionQuery(
    $partitionSetName: String!
    $partitionName: String!
  ) {
    partitionSetOrError(partitionSetName: $partitionSetName) {
      __typename
      ... on PartitionSet {
        partition(partitionName: $partitionName) {
          name
          solidSelection
          runConfigYaml
          mode
          tags {
            key
            value
          }
        }
      }
    }
  }
`;

function usePresetsAndPartitions(
  pipelineName: string
): {
  presets: Preset[];
  partitionSets: PartitionSet[];
  loading: boolean;
  pipeline?: Pipeline;
} {
  const repositorySelector = useRepositorySelector();
  const pipelineSelector = usePipelineSelector(pipelineName);
  const presetsQuery = useQuery<ConfigPresetsQuery>(CONFIG_PRESETS_QUERY, {
    fetchPolicy: "cache-and-network",
    variables: { pipelineSelector }
  });
  const partitionSetsQuery = useQuery<ConfigPartitionSetsQuery>(
    CONFIG_PARTITION_SETS_QUERY,
    {
      fetchPolicy: "cache-and-network",
      variables: { repositorySelector, pipelineName }
    }
  );

  const byName = (a: { name: string }, b: { name: string }) =>
    a.name.localeCompare(b.name);

  return {
    loading: presetsQuery.loading || partitionSetsQuery.loading,
    presets:
      presetsQuery.data?.pipelineOrError?.__typename === "Pipeline"
        ? presetsQuery.data.pipelineOrError.presets.sort(byName)
        : [],
    partitionSets:
      partitionSetsQuery.data?.partitionSetsOrError?.__typename ===
      "PartitionSets"
        ? partitionSetsQuery.data.partitionSetsOrError.results.sort(byName)
        : [],
    pipeline:
      presetsQuery.data?.pipelineOrError?.__typename === "Pipeline"
        ? presetsQuery.data.pipelineOrError
        : undefined
  };
}
