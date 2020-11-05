import {MockList} from '@graphql-tools/mock';
import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {useCurrentRepositoryState, useRepositoryOptions} from 'src/DagsterRepositoryContext';
import {ApolloTestProvider} from 'src/testing/ApolloTestProvider';

describe('DagsterRepositoryContext', () => {
  const Test = () => {
    const {options} = useRepositoryOptions();
    const [repo] = useCurrentRepositoryState(options);
    return <div>Pipeline count: {repo?.repository.pipelines.length}</div>;
  };

  describe('Repository options', () => {
    const defaultMocks = {
      RepositoriesOrError: () => ({
        __typename: 'RepositoryConnection',
      }),
      RepositoryConnection: () => ({
        nodes: () => new MockList(1),
      }),
    };

    it('updates the "current repository" state correctly when the repo itself changes', async () => {
      let numPipelines = 1;
      const mocks = {
        ...defaultMocks,
        Repository: () => ({
          pipelines: () => new MockList(numPipelines),
        }),
      };

      const {rerender} = render(
        <ApolloTestProvider mocks={mocks}>
          <Test key="a" />
        </ApolloTestProvider>,
      );

      await waitFor(() => {
        expect(screen.getByText(/pipeline count: 1/i)).toBeVisible();
      });

      numPipelines++;
      rerender(
        <ApolloTestProvider mocks={mocks}>
          <Test key="b" />
        </ApolloTestProvider>,
      );

      await waitFor(() => {
        expect(screen.getByText(/pipeline count: 2/i)).toBeVisible();
      });

      numPipelines--;
      rerender(
        <ApolloTestProvider mocks={mocks}>
          <Test key="c" />
        </ApolloTestProvider>,
      );

      await waitFor(() => {
        expect(screen.getByText(/pipeline count: 1/i)).toBeVisible();
      });
    });
  });
});
