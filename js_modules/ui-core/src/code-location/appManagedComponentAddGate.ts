interface AddGateInputs {
  isBranchDeployment: boolean;
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
  isBranchDeployment,
  gitProviderConnected,
  gitBackedEnabled,
  bindingLoading,
  hasBinding,
}: AddGateInputs): string | null => {
  // A branch deployment previews the component authored on the pull request.
  // Adding another one there would leave state the pull request never contains,
  // so only edits to the existing draft are allowed.
  if (isBranchDeployment) {
    return 'Components can only be added from the base deployment.';
  }
  if (!gitProviderConnected) {
    return 'Connect a git integration to author components.';
  }
  if (gitBackedEnabled && !bindingLoading && !hasBinding) {
    return 'Set a repository to open pull requests for components created in the UI.';
  }
  return null;
};
