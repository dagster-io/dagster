

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelinesFragment
// ====================================================

export interface PipelinesFragment_solids_output_type {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_output_expectations {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_output_materializations_arguments_type {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_output_materializations_arguments {
  name: string;
  description: string | null;
  type: PipelinesFragment_solids_output_materializations_arguments_type;
  isOptional: boolean;
}

export interface PipelinesFragment_solids_output_materializations {
  name: string;
  description: string | null;
  arguments: PipelinesFragment_solids_output_materializations_arguments[];
}

export interface PipelinesFragment_solids_output {
  type: PipelinesFragment_solids_output_type;
  expectations: PipelinesFragment_solids_output_expectations[];
  materializations: PipelinesFragment_solids_output_materializations[];
}

export interface PipelinesFragment_solids_inputs_type {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_inputs_expectations {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_inputs_sources_arguments_type {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_inputs_sources_arguments {
  name: string;
  description: string | null;
  type: PipelinesFragment_solids_inputs_sources_arguments_type;
  isOptional: boolean;
}

export interface PipelinesFragment_solids_inputs_sources {
  name: string;
  description: string | null;
  arguments: PipelinesFragment_solids_inputs_sources_arguments[];
}

export interface PipelinesFragment_solids_inputs_dependsOn {
  name: string;
}

export interface PipelinesFragment_solids_inputs {
  name: string;
  type: PipelinesFragment_solids_inputs_type;
  expectations: PipelinesFragment_solids_inputs_expectations[];
  description: string | null;
  sources: PipelinesFragment_solids_inputs_sources[];
  dependsOn: PipelinesFragment_solids_inputs_dependsOn | null;
}

export interface PipelinesFragment_solids {
  output: PipelinesFragment_solids_output;
  inputs: PipelinesFragment_solids_inputs[];
  name: string;
  description: string | null;
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