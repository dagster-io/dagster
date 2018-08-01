

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: MaterializationFragment
// ====================================================

export interface MaterializationFragment_arguments {
  name: string;
  description: string | null;
  type: Type;
  isOptional: boolean;
}

export interface MaterializationFragment {
  name: string;
  description: string | null;
  arguments: MaterializationFragment_arguments[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

export enum Type {
  BOOL = "BOOL",
  INT = "INT",
  PATH = "PATH",
  STRING = "STRING",
}

//==============================================================
// END Enums and Input Objects
//==============================================================