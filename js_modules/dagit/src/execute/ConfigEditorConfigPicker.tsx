import * as React from "react";
import { Button, Menu, MenuItem, Icon } from "@blueprintjs/core";
import * as ReactDOM from "react-dom";

import { Select } from "@blueprintjs/select";
import { useQuery } from "react-apollo";
import {
  ConfigPresetsQuery,
  ConfigPresetsQuery_pipeline_presets
} from "./types/ConfigPresetsQuery";
import {
  ConfigPartitionsQuery,
  ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitions
} from "./types/ConfigPartitionsQuery";
import {
  ConfigPartitionSetsQuery,
  ConfigPartitionSetsQuery_partitionSetsOrError_PartitionSets_results
} from "./types/ConfigPartitionSetsQuery";
import gql from "graphql-tag";
import { IExecutionSession } from "../LocalStorage";
import ApolloClient from "apollo-client";
import { isEqual } from "apollo-utilities";
import styled from "styled-components";
import { ShortcutHandler } from "../ShortcutHandler";

type Preset = ConfigPresetsQuery_pipeline_presets;
type PartitionSet = ConfigPartitionSetsQuery_partitionSetsOrError_PartitionSets_results;
type Partition = ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitions;
type ConfigGenerator = Preset | PartitionSet;

const ConfigGeneratorSelect = Select.ofType<ConfigGenerator>();
const PartitionSelect = Select.ofType<Partition>();

interface ConfigEditorConfigPickerProps {
  pipelineName: string;
  solidSubset: string[] | null;
  onCreateSession: (initial: Partial<IExecutionSession>) => void;
}

interface ConfigEditorConfigPickerState {
  selectedConfigGenerator: ConfigGenerator | null;
  selectedPartition: Partition | null;
}

interface ConfigEditorConfigGeneratorPickerProps {
  pipelineName: string;
  solidSubset: string[] | null;
  selectedConfigGenerator: ConfigGenerator | null;
  onCreateSession: (initial: Partial<IExecutionSession>) => void;
  onSelectConfigGenerator: (configGenerator: ConfigGenerator) => void;
}

export class ConfigEditorConfigPicker extends React.Component<
  ConfigEditorConfigPickerProps
> {
  state: Readonly<ConfigEditorConfigPickerState> = {
    selectedConfigGenerator: null,
    selectedPartition: null
  };

  onSelectConfigGenerator = (configGenerator: ConfigGenerator) => {
    this.setState({ selectedConfigGenerator: configGenerator });
    this.setState({ selectedPartition: null });
  };

  onSelectPartition = (partition: Partition) => {
    this.setState({ selectedPartition: partition });
  };

  render() {
    const { selectedConfigGenerator } = this.state;

    return (
      <PickerContainer>
        <ConfigEditorConfigGeneratorPicker
          pipelineName={this.props.pipelineName}
          solidSubset={this.props.solidSubset}
          onCreateSession={this.props.onCreateSession}
          selectedConfigGenerator={this.state.selectedConfigGenerator}
          onSelectConfigGenerator={this.onSelectConfigGenerator}
        />
        {selectedConfigGenerator &&
          selectedConfigGenerator.__typename === "PartitionSet" && (
            <>
              <Icon icon="chevron-right" style={{ padding: "0 10px" }} />
              <ConfigEditorPartitionPicker
                pipelineName={this.props.pipelineName}
                partitionSet={selectedConfigGenerator}
                selectedPartition={this.state.selectedPartition}
                onSelectPartition={this.onSelectPartition}
                onCreateSession={this.props.onCreateSession}
              />
            </>
          )}
      </PickerContainer>
    );
  }
}

interface ConfigEditorPartitionPickerProps {
  pipelineName: string;
  partitionSet: PartitionSet;
  selectedPartition: Partition | null;
  onSelectPartition: (partition: Partition) => void;
  onCreateSession: (initial: Partial<IExecutionSession>) => void;
}

export const ConfigEditorPartitionPicker: React.FunctionComponent<ConfigEditorPartitionPickerProps> = React.memo(
  props => {
    const {
      partitionSet,
      onCreateSession,
      onSelectPartition,
      selectedPartition
    } = props;

    const onPartitionSelect = async (partition: Partition) => {
      onCreateSession({
        name: partition.name,
        environmentConfigYaml: partition.environmentConfigYaml || "",
        solidSubset: partition.solidSubset,
        mode: partition.mode,
        tags: partition.tags
      });
      onSelectPartition(partition);
    };

    const { data } = useQuery<ConfigPartitionsQuery>(CONFIG_PARTITIONS_QUERY, {
      fetchPolicy: "network-only",
      variables: { partitionSetName: partitionSet.name }
    });

    const partitions: Partition[] =
      (data &&
        data.partitionSetOrError.__typename === "PartitionSet" &&
        data.partitionSetOrError.partitions) ||
      [];

    return (
      <div>
        <PartitionSelect
          items={partitions}
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
          onItemSelect={partition => onPartitionSelect(partition)}
        >
          <Button
            text={selectedPartition ? selectedPartition.name : ""}
            icon="insert"
            rightIcon="caret-down"
          />
        </PartitionSelect>
      </div>
    );
  },
  isEqual
);

export const ConfigEditorConfigGeneratorPicker: React.FunctionComponent<ConfigEditorConfigGeneratorPickerProps> = React.memo(
  props => {
    const { pipelineName, onCreateSession, onSelectConfigGenerator } = props;

    const onPresetSelect = async (
      preset: Preset,
      pipelineName: string,
      client: ApolloClient<any>
    ) => {
      const { data } = await client.query({
        query: CONFIG_PRESETS_QUERY,
        variables: { pipelineName },
        fetchPolicy: "network-only"
      });
      let updatedPreset = preset;
      for (const p of data.pipeline.presets) {
        if (p.name === preset.name) {
          updatedPreset = p;
          break;
        }
      }
      onCreateSession({
        name: updatedPreset.name,
        environmentConfigYaml: updatedPreset.environmentConfigYaml || "",
        solidSubset: updatedPreset.solidSubset,
        mode: updatedPreset.mode
      });
      onSelectConfigGenerator(updatedPreset);
    };

    const onPartitionSetSelect = async (partitionSet: PartitionSet) => {
      onSelectConfigGenerator(partitionSet);
    };

    const { data, client } = useQuery<ConfigPresetsQuery>(
      CONFIG_PRESETS_QUERY,
      {
        fetchPolicy: "network-only",
        variables: { pipelineName }
      }
    );

    const presets: Preset[] = (
      (data &&
        data.pipeline &&
        data.pipeline.__typename === "Pipeline" &&
        data.pipeline.presets) ||
      []
    ).sort((a, b) => a.name.localeCompare(b.name));

    const { data: partitionsData } = useQuery<ConfigPartitionSetsQuery>(
      CONFIG_PARTITION_SETS_QUERY,
      {
        fetchPolicy: "network-only",
        variables: { pipelineName }
      }
    );

    const partitionSets: PartitionSet[] =
      (partitionsData &&
        partitionsData.partitionSetsOrError.__typename === "PartitionSets" &&
        partitionsData.partitionSetsOrError.results) ||
      [];

    // This is done in two steps because we can't do
    // presets.concat(partitionsSets) since they are different types
    let configGenerators: ConfigGenerator[] = presets;
    configGenerators = configGenerators.concat(partitionSets);

    const select: React.RefObject<Select<ConfigGenerator>> = React.createRef();

    return (
      <div>
        <ShortcutHandler
          shortcutLabel={"⌥E"}
          shortcutFilter={e => e.keyCode === 69 && e.altKey}
          onShortcut={() => activateSelect(select.current)}
        >
          <ConfigGeneratorSelect
            ref={select}
            items={configGenerators}
            itemPredicate={(query, configGenerator) =>
              query.length === 0 || configGenerator.name.includes(query)
            }
            itemListRenderer={({
              itemsParentRef,
              renderItem,
              filteredItems
            }) => {
              const presetItems = filteredItems.filter(
                item => item.__typename === "PipelinePreset"
              );

              const partitionSetItems = filteredItems.filter(
                item => item.__typename === "PartitionSet"
              );

              const renderedPresetItems = presetItems
                .map(renderItem)
                .filter(item => item != null);

              const renderedPartitionSetItems = partitionSetItems
                .map(renderItem)
                .filter(item => item != null);

              return (
                <Menu ulRef={itemsParentRef}>
                  {renderedPresetItems.length > 0 && (
                    <>
                      <MenuItem disabled={true} text={`Presets`} />
                      {renderedPresetItems}
                    </>
                  )}
                  {renderedPresetItems.length > 0 &&
                    renderedPartitionSetItems.length > 0 && <Menu.Divider />}
                  {renderedPartitionSetItems.length > 0 && (
                    <>
                      <MenuItem disabled={true} text={`Partitions`} />
                      {renderedPartitionSetItems}
                    </>
                  )}
                </Menu>
              );
            }}
            itemRenderer={(configGenerator, props) => (
              <Menu.Item
                active={props.modifiers.active}
                onClick={props.handleClick}
                key={configGenerator.name}
                text={configGenerator.name}
              />
            )}
            noResults={<Menu.Item disabled={true} text="No presets." />}
            onItemSelect={selection => {
              selection.__typename === "PipelinePreset"
                ? onPresetSelect(selection, pipelineName, client)
                : onPartitionSetSelect(selection);
            }}
          >
            <Button
              text={
                props.selectedConfigGenerator
                  ? props.selectedConfigGenerator.name
                  : ""
              }
              title="preset-selector-button"
              icon="insert"
              rightIcon="caret-down"
            />
          </ConfigGeneratorSelect>
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

export const CONFIG_PRESETS_QUERY = gql`
  query ConfigPresetsQuery($pipelineName: String!) {
    pipeline(params: { name: $pipelineName }) {
      name
      presets {
        __typename
        name
        solidSubset
        environmentConfigYaml
        mode
      }
    }
  }
`;

export const CONFIG_PARTITION_SETS_QUERY = gql`
  query ConfigPartitionSetsQuery($pipelineName: String!) {
    partitionSetsOrError(pipelineName: $pipelineName) {
      __typename
      ... on PartitionSets {
        results {
          name
        }
      }
    }
  }
`;

export const CONFIG_PARTITIONS_QUERY = gql`
  query ConfigPartitionsQuery($partitionSetName: String!) {
    partitionSetOrError(partitionSetName: $partitionSetName) {
      __typename
      ... on PartitionSet {
        partitions {
          name
          solidSubset
          environmentConfigYaml
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
