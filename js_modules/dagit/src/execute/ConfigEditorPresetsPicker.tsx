import * as React from "react";
import { isEqual } from "lodash";
import { Button, Menu } from "@blueprintjs/core";
import { Select } from "@blueprintjs/select";
import { Query, QueryResult } from "react-apollo";
import {
  ConfigPresetsQuery,
  ConfigPresetsQuery_presetsForPipeline
} from "./types/ConfigPresetsQuery";
import gql from "graphql-tag";

type Preset = ConfigPresetsQuery_presetsForPipeline;

const SWITCH_SUBSET_MESSAGE = `This preset requires you execute the solid subset below. Would you like to switch to it?\n\n[{{subset}}]`;

const PresetSelect = Select.ofType<Preset>();

const PresetDivider: Preset = {
  __typename: "PipelinePreset",
  name: "divider",
  solidSubset: null,
  environment: null
};

interface ConfigEditorPresetsPickerProps {
  pipelineName: string;
  configCode: string;
  solidSubset: string[] | null;
  onChange: (config: string, solidSubset: string[] | null) => void;
}

export default class ConfigEditorPresetsPicker extends React.Component<
  ConfigEditorPresetsPickerProps
> {
  render() {
    const { pipelineName, configCode, solidSubset, onChange } = this.props;

    return (
      <Query
        query={CONFIG_PRESETS_QUERY}
        fetchPolicy="cache-and-network"
        variables={{ pipelineName }}
      >
        {({ data }: QueryResult<ConfigPresetsQuery, any>) => {
          const presets = ((data && data.presetsForPipeline) || []).sort(
            (a, b) => a.name.localeCompare(b.name)
          );

          let grouped = presets.filter(p =>
            isEqual(p.solidSubset, solidSubset)
          );
          if (grouped.length && grouped.length !== presets.length) {
            grouped.push(PresetDivider);
          }
          grouped.push(
            ...presets.filter(p => !isEqual(p.solidSubset, solidSubset))
          );

          const onItemSelect = (p: Preset) => {
            let desiredSubset = solidSubset;

            if (!isEqual(p.solidSubset, solidSubset)) {
              const desc = p.solidSubset
                ? p.solidSubset.join(", ")
                : "All Solids";
              if (confirm(SWITCH_SUBSET_MESSAGE.replace("{{subset}}", desc))) {
                desiredSubset = p.solidSubset;
              }
            }
            onChange(configCode + "\n" + p.environment, desiredSubset);
          };

          return (
            <div>
              <PresetSelect
                items={grouped}
                itemPredicate={(query, preset) =>
                  query.length === 0 || preset.name.includes(query)
                }
                itemRenderer={(preset, props) =>
                  preset === PresetDivider ? (
                    <Menu.Divider />
                  ) : (
                    <Menu.Item
                      active={props.modifiers.active}
                      onClick={props.handleClick}
                      key={preset.name}
                      text={preset.name}
                    />
                  )
                }
                noResults={<Menu.Item disabled={true} text="No results." />}
                onItemSelect={onItemSelect}
              >
                <Button text={""} icon="insert" rightIcon="caret-down" />
              </PresetSelect>
            </div>
          );
        }}
      </Query>
    );
  }
}

export const CONFIG_PRESETS_QUERY = gql`
  query ConfigPresetsQuery($pipelineName: String!) {
    presetsForPipeline(pipelineName: $pipelineName) {
      solidSubset
      name
      environment
    }
  }
`;
