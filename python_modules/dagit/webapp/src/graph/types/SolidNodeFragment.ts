

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidNodeFragment
// ====================================================

export interface SolidNodeFragment_inputs_type {
  name: string;
}

export interface SolidNodeFragment_inputs_dependsOn_solid {
  name: string;
}

export interface SolidNodeFragment_inputs_dependsOn {
  name: string;
  solid: SolidNodeFragment_inputs_dependsOn_solid;
}

export interface SolidNodeFragment_inputs {
  name: string;
  type: SolidNodeFragment_inputs_type;
  dependsOn: SolidNodeFragment_inputs_dependsOn | null;
}

export interface SolidNodeFragment_outputs_type {
  name: string;
}

export interface SolidNodeFragment_outputs_expectations {
  name: string;
  description: string | null;
}

export interface SolidNodeFragment_outputs {
  name: string;
  type: SolidNodeFragment_outputs_type;
  expectations: SolidNodeFragment_outputs_expectations[];
}

export interface SolidNodeFragment {
  name: string;
  inputs: SolidNodeFragment_inputs[];
  outputs: SolidNodeFragment_outputs[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================