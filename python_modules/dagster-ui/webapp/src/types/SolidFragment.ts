

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidFragment
// ====================================================

export interface SolidFragment_output_type {
  name: string;
  description: string | null;
}

export interface SolidFragment_output_expectations {
  name: string;
  description: string | null;
}

export interface SolidFragment_output_materializations_arguments_type {
  name: string;
  description: string | null;
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

export interface SolidFragment_output {
  type: SolidFragment_output_type;
  expectations: SolidFragment_output_expectations[];
  materializations: SolidFragment_output_materializations[];
}

export interface SolidFragment_inputs_type {
  name: string;
  description: string | null;
}

export interface SolidFragment_inputs_expectations {
  name: string;
  description: string | null;
}

export interface SolidFragment_inputs_sources_arguments_type {
  name: string;
  description: string | null;
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
  name: string;
  type: SolidFragment_inputs_type;
  expectations: SolidFragment_inputs_expectations[];
  description: string | null;
  sources: SolidFragment_inputs_sources[];
  dependsOn: SolidFragment_inputs_dependsOn | null;
}

export interface SolidFragment {
  output: SolidFragment_output;
  inputs: SolidFragment_inputs[];
  name: string;
  description: string | null;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================