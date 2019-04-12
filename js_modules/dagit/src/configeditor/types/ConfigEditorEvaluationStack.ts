/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigEditorEvaluationStack
// ====================================================

export interface ConfigEditorEvaluationStack_entries_EvaluationStackPathEntry_field {
  __typename: "ConfigTypeField";
  name: string;
}

export interface ConfigEditorEvaluationStack_entries_EvaluationStackPathEntry {
  __typename: "EvaluationStackPathEntry";
  field: ConfigEditorEvaluationStack_entries_EvaluationStackPathEntry_field;
}

export interface ConfigEditorEvaluationStack_entries_EvaluationStackListItemEntry {
  __typename: "EvaluationStackListItemEntry";
  listIndex: number;
}

export type ConfigEditorEvaluationStack_entries = ConfigEditorEvaluationStack_entries_EvaluationStackPathEntry | ConfigEditorEvaluationStack_entries_EvaluationStackListItemEntry;

export interface ConfigEditorEvaluationStack {
  __typename: "EvaluationStack";
  entries: ConfigEditorEvaluationStack_entries[];
}
