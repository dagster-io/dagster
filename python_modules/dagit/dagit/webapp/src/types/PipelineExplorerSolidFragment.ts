

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExplorerSolidFragment
// ====================================================

export interface PipelineExplorerSolidFragment_definition_metadata {
  key: string | null;
  value: string | null;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type {
  description: string | null;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition {
  type: PipelineExplorerSolidFragment_definition_configDefinition_type;
}

export interface PipelineExplorerSolidFragment_definition {
  metadata: PipelineExplorerSolidFragment_definition_metadata[] | null;
  configDefinition: PipelineExplorerSolidFragment_definition_configDefinition | null;
}

export interface PipelineExplorerSolidFragment_inputs_definition_type {
  name: string;
}

export interface PipelineExplorerSolidFragment_inputs_definition {
  name: string;
  type: PipelineExplorerSolidFragment_inputs_definition_type;
}

export interface PipelineExplorerSolidFragment_inputs_dependsOn_definition {
  name: string;
}

export interface PipelineExplorerSolidFragment_inputs_dependsOn_solid {
  name: string;
}

export interface PipelineExplorerSolidFragment_inputs_dependsOn {
  definition: PipelineExplorerSolidFragment_inputs_dependsOn_definition;
  solid: PipelineExplorerSolidFragment_inputs_dependsOn_solid;
}

export interface PipelineExplorerSolidFragment_inputs {
  definition: PipelineExplorerSolidFragment_inputs_definition;
  dependsOn: PipelineExplorerSolidFragment_inputs_dependsOn | null;
}

export interface PipelineExplorerSolidFragment_outputs_definition_type {
  name: string;
}

export interface PipelineExplorerSolidFragment_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelineExplorerSolidFragment_outputs_definition {
  name: string;
  type: PipelineExplorerSolidFragment_outputs_definition_type;
  expectations: PipelineExplorerSolidFragment_outputs_definition_expectations[];
}

export interface PipelineExplorerSolidFragment_outputs {
  definition: PipelineExplorerSolidFragment_outputs_definition;
}

export interface PipelineExplorerSolidFragment {
  name: string;
  definition: PipelineExplorerSolidFragment_definition;
  inputs: PipelineExplorerSolidFragment_inputs[];
  outputs: PipelineExplorerSolidFragment_outputs[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================