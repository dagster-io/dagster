import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {useGitProviderConnected} from '@shared/app/useGitProviderConnected';
import {useOpenAppManagedComponentPullRequest} from '@shared/code-location/useOpenAppManagedComponentPullRequest';
import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import {buildComponentTypeInfo, buildComponentTypes} from '../../graphql/builders';
import {AppManagedComponentTypePickerDialog} from '../AppManagedComponentTypePickerDialog';
import {CODE_LOCATION_COMPONENT_TYPES_QUERY} from '../CodeLocationComponentTypesQuery';
import {OpenComponentPullRequestResult} from '../appManagedComponentPullRequest';
import {
  CodeLocationComponentTypesQuery,
  CodeLocationComponentTypesQueryVariables,
} from '../types/CodeLocationComponentTypesQuery.types';

// Unit tested separately; stub it so the form reports a valid component.
jest.mock('../AppManagedComponentEditorBody', () => {
  const {useEffect} = jest.requireActual('react');
  return {
    AppManagedComponentEditorBody: ({
      onChange,
    }: {
      onChange: (state: {componentId: string; attributes: string; isValid: boolean}) => void;
    }) => {
      useEffect(() => {
        onChange({componentId: 'my_component', attributes: 'foo: bar\n', isValid: true});
      }, [onChange]);
      return <div />;
    },
  };
});

jest.mock('@shared/app/useGitProviderConnected', () => ({
  useGitProviderConnected: jest.fn(),
}));

jest.mock('@shared/code-location/useOpenAppManagedComponentPullRequest', () => ({
  useOpenAppManagedComponentPullRequest: jest.fn(),
}));

const gitProviderConnectedMock = useGitProviderConnected as jest.Mock;
const openPullRequestHookMock = useOpenAppManagedComponentPullRequest as jest.Mock;

const LOCATION_NAME = 'my_location';

const componentTypesMock: MockedResponse<
  CodeLocationComponentTypesQuery,
  CodeLocationComponentTypesQueryVariables
> = {
  request: {
    query: CODE_LOCATION_COMPONENT_TYPES_QUERY,
    variables: {locationName: LOCATION_NAME},
  },
  result: {
    data: {
      __typename: 'Query',
      componentTypesForLocationOrError: buildComponentTypes({
        locationName: LOCATION_NAME,
        componentTypes: [
          buildComponentTypeInfo({
            name: 'MyComponent',
            namespace: 'my_lib.components',
            description: 'Does a thing.',
            isAppManaged: true,
          }),
        ],
      }),
    },
  },
};

function renderDialog() {
  return render(
    <MockedProvider mocks={[componentTypesMock]}>
      <AppManagedComponentTypePickerDialog
        isOpen
        onClose={jest.fn()}
        onFailed={jest.fn()}
        onCreated={jest.fn()}
        locationName={LOCATION_NAME}
      />
    </MockedProvider>,
  );
}

describe('AppManagedComponentTypePickerDialog', () => {
  it('names the pull request on submit and says so before the user submits', async () => {
    gitProviderConnectedMock.mockReturnValue(true);
    openPullRequestHookMock.mockReturnValue(jest.fn());

    const user = userEvent.setup();
    renderDialog();
    await user.click(await screen.findByRole('button', {name: 'Configure'}));

    expect(await screen.findByRole('button', {name: 'Open pull request'})).toBeEnabled();
    expect(screen.getByText(/Submitting opens a pull request/)).toBeVisible();
  });

  it('keeps the live-write label and no pull request note when not git-backed', async () => {
    gitProviderConnectedMock.mockReturnValue(false);
    openPullRequestHookMock.mockReturnValue(null);

    const user = userEvent.setup();
    renderDialog();
    await user.click(await screen.findByRole('button', {name: 'Configure'}));

    expect(await screen.findByRole('button', {name: 'Add component'})).toBeEnabled();
    expect(screen.queryByText(/Submitting opens a pull request/)).toBeNull();
  });

  it('shows progress and disables the footer while the pull request is opening', async () => {
    gitProviderConnectedMock.mockReturnValue(true);
    let resolvePullRequest: (result: OpenComponentPullRequestResult) => void = () => {};
    openPullRequestHookMock.mockReturnValue(
      jest.fn(
        () =>
          new Promise<OpenComponentPullRequestResult>((resolve) => {
            resolvePullRequest = resolve;
          }),
      ),
    );

    const user = userEvent.setup();
    renderDialog();
    await user.click(await screen.findByRole('button', {name: 'Configure'}));
    await user.click(await screen.findByRole('button', {name: 'Open pull request'}));

    expect(await screen.findByRole('button', {name: 'Opening pull request…'})).toBeDisabled();
    expect(screen.getByRole('button', {name: 'Cancel'})).toBeDisabled();

    resolvePullRequest({status: 'error', message: 'Could not open a pull request'});

    expect(await screen.findByText('Could not open a pull request')).toBeVisible();
    expect(await screen.findByRole('button', {name: 'Open pull request'})).toBeEnabled();
  });
});
