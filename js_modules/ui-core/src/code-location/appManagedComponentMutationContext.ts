// Carries enough state about a UI-component mutation that just succeeded at
// the storage layer (but may have failed during the in-process reload) to
// surface a revert action. ``prevAttributes`` is the YAML present *before* the
// mutation: needed to restore an edit or recreate a delete, and absent for
// adds (revert = delete the just-added component).

export interface AppManagedComponentMutationContext {
  kind: 'add' | 'edit' | 'delete';
  componentId: string;
  componentType: string;
  prevAttributes?: string;
}
