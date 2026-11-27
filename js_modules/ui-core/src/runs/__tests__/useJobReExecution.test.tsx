import {MockLink, MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter, useLocation} from 'react-router-dom';

import {ApolloLink} from '../../apollo-client';
import {CustomAlertProvider} from '../../app/CustomAlertProvider';
import {ReexecutionStrategy} from '../../graphql/types';
import {UI_EXECUTION_TAGS} from '../../launchpad/uiExecutionTags';
import {testId} from '../../testing/testId';
import {
  buildLaunchPipelineReexecutionErrorMock,
  buildLaunchPipelineReexecutionSuccessMock,
} from '../__fixtures__/Reexecution.fixtures';
import {useJobReexecution} from '../useJobReExecution';

const Wrapper = (props: {
  reexecuteParams: Parameters<ReturnType<typeof useJobReexecution>['onClick']>;
}) => {
  const reexecute = useJobReexecution();
  const location = useLocation();
  return (
    <>
      {reexecute.launchpadElement}
      <button onClick={() => reexecute.onClick(...props.reexecuteParams)}>Re-execute</button>
      <div data-testid={testId('location')}>{location.pathname}</div>
    </>
  );
};

const windowOpenSpy = jest.spyOn(window, 'open').mockImplementation(() => null);

describe('useJobReexecution', () => {
  const PARENT_RUN = {id: '1', pipelineName: 'abc', tags: []};

  afterEach(() => {
    windowOpenSpy.mockClear();
  });

  it('creates the correct mutation for FROM_FAILURE', async () => {
    const user = userEvent.setup();
    const {findByText, findByTestId} = render(
      <MockedProvider
        addTypename={false}
        mocks={[
          buildLaunchPipelineReexecutionSuccessMock({
            parentRunId: '1',
            strategy: ReexecutionStrategy.FROM_FAILURE,
            extraTags: UI_EXECUTION_TAGS,
          }),
        ]}
      >
        <MemoryRouter>
          <Wrapper reexecuteParams={[PARENT_RUN, ReexecutionStrategy.FROM_FAILURE, false]} />
        </MemoryRouter>
      </MockedProvider>,
    );

    await user.click(await findByText('Re-execute'));

    expect((await findByTestId('location')).textContent).toEqual('/runs/1234');
  });

  it('shows the re-execute dialog so you can provide tags if requested', async () => {
    const user = userEvent.setup();
    const {findByText} = render(
      <MockedProvider
        addTypename={false}
        mocks={[
          buildLaunchPipelineReexecutionSuccessMock({
            parentRunId: '1',
            extraTags: [{key: 'test_key', value: 'test_value'}, ...UI_EXECUTION_TAGS],
          }),
        ]}
      >
        <MemoryRouter>
          <Wrapper reexecuteParams={[PARENT_RUN, ReexecutionStrategy.FROM_FAILURE, true]} />
        </MemoryRouter>
      </MockedProvider>,
    );

    await user.click(await findByText('Re-execute'));

    await user.click(await screen.findByText('Add custom tag'));
    await user.type(await screen.findByPlaceholderText('Tag Key'), 'test_key');
    await user.type(await screen.findByPlaceholderText('Tag Value'), 'test_value');

    await waitFor(async () => {
      const button = screen.getByText(/re\-execute 1 run/i);
      await user.click(button);
    });

    await waitFor(() => {
      expect(screen.getByText(/Successfully requested re-execution for 1 run./i)).toBeVisible();
    });
  });

  it('opens in a new tab when openInNewTab option is provided', async () => {
    const user = userEvent.setup();
    const {findByText, findByTestId} = render(
      <MockedProvider
        addTypename={false}
        mocks={[
          buildLaunchPipelineReexecutionSuccessMock({
            parentRunId: '1',
            strategy: ReexecutionStrategy.FROM_FAILURE,
            extraTags: UI_EXECUTION_TAGS,
          }),
        ]}
      >
        <MemoryRouter>
          <Wrapper
            reexecuteParams={[
              PARENT_RUN,
              ReexecutionStrategy.FROM_FAILURE,
              false,
              {openInNewTab: true},
            ]}
          />
        </MemoryRouter>
      </MockedProvider>,
    );

    await user.click(await findByText('Re-execute'));

    await waitFor(() => {
      expect(windowOpenSpy).toHaveBeenCalledWith('/runs/1234', '_blank');
    });

    // Should NOT navigate in the same tab
    expect((await findByTestId('location')).textContent).toEqual('/');
  });

  it('launches once when clicked again while a launch is in flight', async () => {
    const user = userEvent.setup();
    // Count launch requests as they are sent, since the mock only responds after a delay.
    const launches = jest.fn();
    const countLink = new ApolloLink((operation, forward) => {
      if (operation.operationName === 'LaunchPipelineReexecution') {
        launches();
      }
      return forward(operation);
    });
    const mockLink = new MockLink([
      {
        ...buildLaunchPipelineReexecutionSuccessMock({
          parentRunId: '1',
          strategy: ReexecutionStrategy.FROM_FAILURE,
          extraTags: UI_EXECUTION_TAGS,
        }),
        maxUsageCount: 2,
        delay: 100,
      },
    ]);
    render(
      <MockedProvider link={ApolloLink.from([countLink, mockLink])}>
        <MemoryRouter>
          <Wrapper reexecuteParams={[PARENT_RUN, ReexecutionStrategy.FROM_FAILURE, false]} />
        </MemoryRouter>
      </MockedProvider>,
    );

    const button = await screen.findByText('Re-execute');
    await user.click(button);
    await user.click(button);
    expect(launches).toHaveBeenCalledTimes(1);

    await waitFor(() => {
      expect(screen.getByTestId('location').textContent).toEqual('/runs/1234');
    });
    expect(launches).toHaveBeenCalledTimes(1);
  });

  it('launches again after a failed launch', async () => {
    const user = userEvent.setup();
    const launches = jest.fn();
    const countLink = new ApolloLink((operation, forward) => {
      if (operation.operationName === 'LaunchPipelineReexecution') {
        launches();
      }
      return forward(operation);
    });
    const mockLink = new MockLink([
      {
        ...buildLaunchPipelineReexecutionErrorMock({
          parentRunId: '1',
          strategy: ReexecutionStrategy.FROM_FAILURE,
          extraTags: UI_EXECUTION_TAGS,
        }),
        maxUsageCount: 2,
      },
    ]);
    render(
      <MockedProvider link={ApolloLink.from([countLink, mockLink])}>
        <MemoryRouter>
          <CustomAlertProvider />
          <Wrapper reexecuteParams={[PARENT_RUN, ReexecutionStrategy.FROM_FAILURE, false]} />
        </MemoryRouter>
      </MockedProvider>,
    );

    const button = await screen.findByText('Re-execute');
    await user.click(button);
    expect(await screen.findByText('A wild python error appeared!')).toBeVisible();
    expect(launches).toHaveBeenCalledTimes(1);

    // The failure released the in-flight guard, so the next click is a new launch attempt.
    await user.click(button);
    await waitFor(() => expect(launches).toHaveBeenCalledTimes(2));
  });

  it('does not open in a new tab when openInNewTab is false', async () => {
    const user = userEvent.setup();
    const {findByText, findByTestId} = render(
      <MockedProvider
        addTypename={false}
        mocks={[
          buildLaunchPipelineReexecutionSuccessMock({
            parentRunId: '1',
            strategy: ReexecutionStrategy.FROM_FAILURE,
            extraTags: UI_EXECUTION_TAGS,
          }),
        ]}
      >
        <MemoryRouter>
          <Wrapper
            reexecuteParams={[
              PARENT_RUN,
              ReexecutionStrategy.FROM_FAILURE,
              false,
              {openInNewTab: false},
            ]}
          />
        </MemoryRouter>
      </MockedProvider>,
    );

    await user.click(await findByText('Re-execute'));

    expect((await findByTestId('location')).textContent).toEqual('/runs/1234');
    expect(windowOpenSpy).not.toHaveBeenCalled();
  });
});
