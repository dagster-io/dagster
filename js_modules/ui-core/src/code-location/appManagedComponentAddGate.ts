interface AddGateInputs {
  gitProviderConnected: boolean;
  gitBackedEnabled: boolean;
  bindingLoading: boolean;
  hasBinding: boolean;
}

/**
 * Why the "Add component" action is unavailable, or null when it's available.
 *
 * A repo binding is only required when the submit would open a pull request
 * (git-backed): with the feature gate off, authoring writes component state
 * directly and needs no repo.
 */
export const addComponentDisabledReason = ({
  gitProviderConnected,
  gitBackedEnabled,
  bindingLoading,
  hasBinding,
}: AddGateInputs): string | null => {
  if (!gitProviderConnected) {
    return 'Connect a git integration to author components.';
  }
  if (gitBackedEnabled && !bindingLoading && !hasBinding) {
    return 'Set a repository to open pull requests for components created in the UI.';
  }
  return null;
};
