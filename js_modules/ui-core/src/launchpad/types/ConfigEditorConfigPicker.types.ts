// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ConfigEditorGeneratorPipelineFragment = {
  __typename: 'Pipeline';
  id: string;
  isJob: boolean;
  name: string;
  presets: Array<{
    __typename: 'PipelinePreset';
    name: string;
    mode: string;
    solidSelection: Array<string> | null;
    runConfigYaml: string;
    tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
  }>;
  tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
};

export type ConfigEditorPipelinePresetFragment = {
  __typename: 'PipelinePreset';
  name: string;
  mode: string;
  solidSelection: Array<string> | null;
  runConfigYaml: string;
  tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
};

export type ConfigEditorGeneratorPartitionSetsFragment = {
  __typename: 'PartitionSets';
  results: Array<{
    __typename: 'PartitionSet';
    id: string;
    name: string;
    mode: string;
    solidSelection: Array<string> | null;
  }>;
};

export type PartitionSetForConfigEditorFragment = {
  __typename: 'PartitionSet';
  id: string;
  name: string;
  mode: string;
  solidSelection: Array<string> | null;
};
