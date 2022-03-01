import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {TestProvider} from '../testing/TestProvider';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {PipelineReference, Props as PipelineReferenceProps} from './PipelineReference';

describe('PipelineReference', () => {
  const Test = (props: PipelineReferenceProps) => (
    <TestProvider>
      <PipelineReference {...props} />
    </TestProvider>
  );

  describe('Job name truncation', () => {
    const props: PipelineReferenceProps = {
      pipelineName: 'foobar',
      pipelineHrefContext: 'repo-unknown',
      isJob: true,
    };

    it('does not truncate job name if below threshold', async () => {
      render(<Test {...props} />);
      await waitFor(() => {
        expect(screen.getByRole('link', {name: /foobar/i})).toBeVisible();
      });
    });

    it('truncates job name if above threshold, buffering back a bit', async () => {
      render(<Test {...props} pipelineName="washington_adams_jefferson_madison_monroe" />);
      await waitFor(() => {
        expect(
          screen.getByRole('link', {name: /washington_adams_jefferson_madison_…/i}),
        ).toBeVisible();
      });
    });
  });

  describe('Links', () => {
    const props: PipelineReferenceProps = {
      pipelineName: 'foobar',
      pipelineHrefContext: 'repo-unknown',
      isJob: true,
    };

    it('if `repo-unknown`, links to job disambiguation page', async () => {
      render(<Test {...props} />);
      await waitFor(() => {
        const link = screen.getByRole('link', {name: /foobar/i});
        expect(link).toBeVisible();
        expect(link.getAttribute('href')).toBe('/workspace/jobs/foobar/');
      });
    });

    it('if RepoAddress, links to job within repo', async () => {
      render(<Test {...props} pipelineHrefContext={buildRepoAddress('lorem', 'ipsum')} />);
      await waitFor(() => {
        const link = screen.getByRole('link', {name: /foobar/i});
        expect(link).toBeVisible();
        expect(link.getAttribute('href')).toBe('/workspace/lorem@ipsum/jobs/foobar/');
      });
    });

    it('if `no-link`, renders plain text', async () => {
      render(<Test {...props} pipelineHrefContext="no-link" />);
      await waitFor(() => {
        const link = screen.queryByRole('link', {name: /foobar/i});
        expect(link).toBeNull();
        expect(screen.getByText('foobar')).toBeVisible();
      });
    });
  });
});
