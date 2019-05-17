import * as React from "react";
import { Button, Menu } from "@blueprintjs/core";
import { Select } from "@blueprintjs/select";
import { Query, QueryResult } from "react-apollo";
import {
  ConfigPresetsQuery,
  ConfigPresetsQuery_pipeline_presets
} from "./types/ConfigPresetsQuery";
import gql from "graphql-tag";
import { IExecutionSession } from "../LocalStorage";

type Preset = ConfigPresetsQuery_pipeline_presets;

const PresetSelect = Select.ofType<Preset>();

interface ConfigEditorPresetsPickerProps {
  pipelineName: string;
  solidSubset: string[] | null;
  onCreateSession: (initial: Partial<IExecutionSession>) => void;
}

// TODO: How to handle mode in the presets picker?
export default class ConfigEditorPresetsPicker extends React.Component<
  ConfigEditorPresetsPickerProps
> {
  render() {
    const { pipelineName, solidSubset, onCreateSession } = this.props;

    return (
      <Query
        query={CONFIG_PRESETS_QUERY}
        fetchPolicy="cache-and-network"
        variables={{ pipelineName }}
      >
        {({ data }: QueryResult<ConfigPresetsQuery, any>) => {
          const presets = (
            (data && data.pipeline && data.pipeline.presets) ||
            []
          ).sort((a, b) => a.name.localeCompare(b.name));

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
                onItemSelect={p =>
                  onCreateSession({
                    name: p.name,
                    config: p.environment || "",
                    solidSubset: p.solidSubset
                  })
                }
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
    pipeline(params: { name: $pipelineName }) {
      name
      presets {
        name
        solidSubset
        environment
      }
    }
  }
`;
