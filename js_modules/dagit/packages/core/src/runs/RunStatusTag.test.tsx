import {render, screen} from '@testing-library/react';
import React from 'react';

import {PipelineRunStatus} from '../types/globalTypes';

import {RunStatusTag} from './RunStatusTag';

describe('RunStatusTag', () => {
  describe('Status type', () => {
    it('renders `succeeded`', () => {
      render(<RunStatusTag status={PipelineRunStatus.SUCCESS} />);
      expect(screen.getByText(/success/i)).toBeVisible();
    });

    it('renders `failed`', () => {
      render(<RunStatusTag status={PipelineRunStatus.FAILURE} />);
      expect(screen.getByText(/failure/i)).toBeVisible();
    });

    it('renders `started`', () => {
      render(<RunStatusTag status={PipelineRunStatus.STARTED} />);
      expect(screen.getByText(/started/i)).toBeVisible();
    });
  });
});
