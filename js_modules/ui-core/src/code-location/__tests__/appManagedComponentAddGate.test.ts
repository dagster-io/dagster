import {addComponentDisabledReason} from '../appManagedComponentAddGate';

const inputs = (overrides: Partial<Parameters<typeof addComponentDisabledReason>[0]> = {}) => ({
  gitProviderConnected: true,
  gitBackedEnabled: true,
  bindingLoading: false,
  hasBinding: true,
  ...overrides,
});

describe('addComponentDisabledReason', () => {
  it('allows authoring when git-backed and the location is bound', () => {
    expect(addComponentDisabledReason(inputs())).toBeNull();
  });

  it('blocks when no git integration is connected', () => {
    expect(addComponentDisabledReason(inputs({gitProviderConnected: false}))).toMatch(
      /Connect a git integration/,
    );
  });

  it('blocks when git-backed and the location has no binding', () => {
    expect(addComponentDisabledReason(inputs({hasBinding: false}))).toMatch(/Set a repository/);
  });

  // Without the gate the submit writes component state directly, so a repo
  // binding is irrelevant and authoring must stay available.
  it('allows authoring with no binding when the feature gate is off', () => {
    expect(
      addComponentDisabledReason(inputs({gitBackedEnabled: false, hasBinding: false})),
    ).toBeNull();
  });

  // Avoids flashing a disabled button before the binding query resolves.
  it('allows authoring while the binding is still loading', () => {
    expect(
      addComponentDisabledReason(inputs({bindingLoading: true, hasBinding: false})),
    ).toBeNull();
  });
});
