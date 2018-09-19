

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidNodeFragment
// ====================================================

export interface SolidNodeFragment_inputs_definition_type {
  name: string;
}

export interface SolidNodeFragment_inputs_definition {
  name: string;
  type: SolidNodeFragment_inputs_definition_type;
}

export interface SolidNodeFragment_inputs_dependsOn_definition {
  name: string;
}

export interface SolidNodeFragment_inputs_dependsOn_solid {
  name: string;
}

export interface SolidNodeFragment_inputs_dependsOn {
  definition: SolidNodeFragment_inputs_dependsOn_definition;
  solid: SolidNodeFragment_inputs_dependsOn_solid;
}

export interface SolidNodeFragment_inputs {
  definition: SolidNodeFragment_inputs_definition;
  dependsOn: SolidNodeFragment_inputs_dependsOn | null;
}

export interface SolidNodeFragment_outputs_definition_type {
  name: string;
}

export interface SolidNodeFragment_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface SolidNodeFragment_outputs_definition {
  name: string;
  type: SolidNodeFragment_outputs_definition_type;
  expectations: SolidNodeFragment_outputs_definition_expectations[];
}

export interface SolidNodeFragment_outputs {
  definition: SolidNodeFragment_outputs_definition;
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