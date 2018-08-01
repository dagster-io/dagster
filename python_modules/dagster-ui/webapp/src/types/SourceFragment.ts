

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SourceFragment
// ====================================================

export interface SourceFragment_arguments {
  name: string;
  description: string | null;
  type: Type;
  isOptional: boolean;
}

export interface SourceFragment {
  name: string;
  description: string | null;
  arguments: SourceFragment_arguments[];
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