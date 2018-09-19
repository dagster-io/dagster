

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidListItemFragment
// ====================================================

export interface SolidListItemFragment_definition {
  description: string | null;
}

export interface SolidListItemFragment_outputs_definition_type {
  name: string;
  description: string | null;
}

export interface SolidListItemFragment_outputs_definition {
  name: string;
  type: SolidListItemFragment_outputs_definition_type;
}

export interface SolidListItemFragment_outputs {
  definition: SolidListItemFragment_outputs_definition;
}

export interface SolidListItemFragment_inputs_definition_type {
  name: string;
  description: string | null;
}

export interface SolidListItemFragment_inputs_definition {
  name: string;
  type: SolidListItemFragment_inputs_definition_type;
}

export interface SolidListItemFragment_inputs {
  definition: SolidListItemFragment_inputs_definition;
}

export interface SolidListItemFragment {
  name: string;
  definition: SolidListItemFragment_definition;
  outputs: SolidListItemFragment_outputs[];
  inputs: SolidListItemFragment_inputs[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================