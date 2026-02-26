import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter, useLocation} from 'react-router-dom';

import {ReexecutionStrategy} from '../../graphql/types';
import {UI_EXECUTION_TAGS} from '../../launchpad/uiExecutionTags';
import {testId} from '../../testing/testId';
import {buildLaunchPipelineReexecutionSuccessMock} from '../__fixtures__/Reexecution.fixtures';
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

describe('useJobReexecution', () => {
  const PARENT_RUN = {id: '1', pipelineName: 'abc', tags: []};

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
});
