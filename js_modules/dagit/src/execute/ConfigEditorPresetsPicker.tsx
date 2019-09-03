import * as React from "react";
import { Button, Menu } from "@blueprintjs/core";
import { Select } from "@blueprintjs/select";
import { useQuery } from "react-apollo";
import {
  ConfigPresetsQuery,
  ConfigPresetsQuery_pipeline_presets
} from "./types/ConfigPresetsQuery";
import gql from "graphql-tag";
import { IExecutionSession } from "../LocalStorage";
import ApolloClient from "apollo-client";

type Preset = ConfigPresetsQuery_pipeline_presets;

const PresetSelect = Select.ofType<Preset>();

interface ConfigEditorPresetsPickerProps {
  pipelineName: string;
  solidSubset: string[] | null;
  onCreateSession: (initial: Partial<IExecutionSession>) => void;
}

export const ConfigEditorPresetsPicker: React.FunctionComponent<
  ConfigEditorPresetsPickerProps
> = props => {
  const { pipelineName, onCreateSession } = props;

  const onPresetSelect = async (
    preset: ConfigPresetsQuery_pipeline_presets,
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
  };

  const { data, client } = useQuery<ConfigPresetsQuery>(CONFIG_PRESETS_QUERY, {
    fetchPolicy: "network-only",
    variables: { pipelineName }
  });
  const presets = ((data && data.pipeline && data.pipeline.presets) || []).sort(
    (a, b) => a.name.localeCompare(b.name)
  );

  return (
    <div>
      <PresetSelect
        items={presets}
        itemPredicate={(query, preset) =>
          query.length === 0 || preset.name.includes(query)
        }
        itemRenderer={(preset, props) => (
          <Menu.Item
            active={props.modifiers.active}
            onClick={props.handleClick}
            key={preset.name}
            text={preset.name}
          />
        )}
        noResults={<Menu.Item disabled={true} text="No presets." />}
        onItemSelect={preset => onPresetSelect(preset, pipelineName, client)}
      >
        <Button text={""} icon="insert" rightIcon="caret-down" />
      </PresetSelect>
    </div>
  );
};

export const CONFIG_PRESETS_QUERY = gql`
  query ConfigPresetsQuery($pipelineName: String!) {
    pipeline(params: { name: $pipelineName }) {
      name
      presets {
        name
        solidSubset
        environmentConfigYaml
        mode
      }
    }
  }
`;
