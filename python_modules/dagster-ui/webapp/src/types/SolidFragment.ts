

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidFragment
// ====================================================

export interface SolidFragment_inputs_type {
  name: string;
  description: string | null;
}

export interface SolidFragment_inputs_sources_arguments_type {
  name: string;
}

export interface SolidFragment_inputs_sources_arguments {
  name: string;
  description: string | null;
  type: SolidFragment_inputs_sources_arguments_type;
  isOptional: boolean;
}

export interface SolidFragment_inputs_sources {
  name: string;
  description: string | null;
  arguments: SolidFragment_inputs_sources_arguments[];
}

export interface SolidFragment_inputs_dependsOn {
  name: string;
}

export interface SolidFragment_inputs {
  type: SolidFragment_inputs_type;
  name: string;
  description: string | null;
  sources: SolidFragment_inputs_sources[];
  dependsOn: SolidFragment_inputs_dependsOn | null;
}

export interface SolidFragment_output_type {
  name: string;
  description: string | null;
}

export interface SolidFragment_output_materializations_arguments_type {
  name: string;
}

export interface SolidFragment_output_materializations_arguments {
  name: string;
  description: string | null;
  type: SolidFragment_output_materializations_arguments_type;
  isOptional: boolean;
}

export interface SolidFragment_output_materializations {
  name: string;
  description: string | null;
  arguments: SolidFragment_output_materializations_arguments[];
}

export interface SolidFragment_output_expectations {
  name: string;
  description: string | null;
}

export interface SolidFragment_output {
  type: SolidFragment_output_type;
  materializations: SolidFragment_output_materializations[];
  expectations: SolidFragment_output_expectations[];
}

export interface SolidFragment {
  name: string;
  description: string | null;
  inputs: SolidFragment_inputs[];
  output: SolidFragment_output;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================