

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelinesFragment
// ====================================================

export interface PipelinesFragment_solids_outputs_type {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_outputs_expectations {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_outputs {
  name: string;
  type: PipelinesFragment_solids_outputs_type;
  description: string | null;
  expectations: PipelinesFragment_solids_outputs_expectations[];
}

export interface PipelinesFragment_solids_inputs_type {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_inputs_expectations {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_inputs_dependsOn_solid {
  name: string;
}

export interface PipelinesFragment_solids_inputs_dependsOn {
  name: string;
  solid: PipelinesFragment_solids_inputs_dependsOn_solid;
}

export interface PipelinesFragment_solids_inputs {
  name: string;
  type: PipelinesFragment_solids_inputs_type;
  description: string | null;
  expectations: PipelinesFragment_solids_inputs_expectations[];
  dependsOn: PipelinesFragment_solids_inputs_dependsOn | null;
}

export interface PipelinesFragment_solids_config_type {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_config {
  name: string;
  description: string | null;
  type: PipelinesFragment_solids_config_type;
  isOptional: boolean;
}

export interface PipelinesFragment_solids {
  outputs: PipelinesFragment_solids_outputs[];
  inputs: PipelinesFragment_solids_inputs[];
  name: string;
  description: string | null;
  config: PipelinesFragment_solids_config[];
}

export interface PipelinesFragment_context_arguments_type {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_context_arguments {
  name: string;
  description: string | null;
  type: PipelinesFragment_context_arguments_type;
  isOptional: boolean;
}

export interface PipelinesFragment_context {
  name: string;
  description: string | null;
  arguments: PipelinesFragment_context_arguments[];
}

export interface PipelinesFragment {
  name: string;
  description: string | null;
  solids: PipelinesFragment_solids[];
  context: PipelinesFragment_context[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================