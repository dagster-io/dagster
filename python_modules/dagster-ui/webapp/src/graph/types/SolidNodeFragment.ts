

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidNodeFragment
// ====================================================

export interface SolidNodeFragment_inputs_type {
  name: string;
}

export interface SolidNodeFragment_inputs_sources {
  name: string;
}

export interface SolidNodeFragment_inputs_dependsOn {
  name: string;
}

export interface SolidNodeFragment_inputs {
  name: string;
  type: SolidNodeFragment_inputs_type;
  sources: SolidNodeFragment_inputs_sources[];
  dependsOn: SolidNodeFragment_inputs_dependsOn | null;
}

export interface SolidNodeFragment_output_type {
  name: string;
}

export interface SolidNodeFragment_output_materializations {
  name: string;
}

export interface SolidNodeFragment_output_expectations {
  name: string;
  description: string | null;
}

export interface SolidNodeFragment_output {
  type: SolidNodeFragment_output_type;
  materializations: SolidNodeFragment_output_materializations[];
  expectations: SolidNodeFragment_output_expectations[];
}

export interface SolidNodeFragment {
  name: string;
  inputs: SolidNodeFragment_inputs[];
  output: SolidNodeFragment_output;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================