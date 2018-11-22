

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidTypeSignatureFragment
// ====================================================

export interface SolidTypeSignatureFragment_outputs_definition_type {
  name: string;
  description: string | null;
}

export interface SolidTypeSignatureFragment_outputs_definition {
  name: string;
  type: SolidTypeSignatureFragment_outputs_definition_type;
}

export interface SolidTypeSignatureFragment_outputs {
  definition: SolidTypeSignatureFragment_outputs_definition;
}

export interface SolidTypeSignatureFragment_inputs_definition_type {
  name: string;
  description: string | null;
}

export interface SolidTypeSignatureFragment_inputs_definition {
  name: string;
  type: SolidTypeSignatureFragment_inputs_definition_type;
}

export interface SolidTypeSignatureFragment_inputs {
  definition: SolidTypeSignatureFragment_inputs_definition;
}

export interface SolidTypeSignatureFragment {
  outputs: SolidTypeSignatureFragment_outputs[];
  inputs: SolidTypeSignatureFragment_inputs[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

/**
 * 
 */
export interface PipelineExecutionParams {
  pipelineName: string;
  config?: any | null;
}

//==============================================================
// END Enums and Input Objects
//==============================================================