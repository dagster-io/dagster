import {render, screen} from '@testing-library/react';
import React from 'react';

import {RunStatusTag} from 'src/runs/RunStatusTag';
import {PipelineRunStatus} from 'src/types/globalTypes';

describe('RunStatusTag', () => {
  describe('Status type', () => {
    it('renders `succeeded`', () => {
      render(<RunStatusTag status={PipelineRunStatus.SUCCESS} />);
      expect(screen.getByText(/succeeded/i)).toBeVisible();
    });

    it('renders `failed`', () => {
      render(<RunStatusTag status={PipelineRunStatus.FAILURE} />);
      expect(screen.getByText(/failed/i)).toBeVisible();
    });

    it('renders `started`', () => {
      render(<RunStatusTag status={PipelineRunStatus.STARTED} />);
      expect(screen.getByText(/started/i)).toBeVisible();
    });
  });
});
