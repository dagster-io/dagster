import {render, screen} from '@testing-library/react';
import React from 'react';

import {RunStatusTag} from 'src/runs/RunStatusTag';

describe('RunStatusTag', () => {
  describe('Status type', () => {
    it('renders `succeeded`', () => {
      render(<RunStatusTag runId="foo" status="SUCCESS" />);
      expect(screen.getByText(/succeeded/i)).toBeVisible();
    });

    it('renders `failed`', () => {
      render(<RunStatusTag runId="foo" status="FAILURE" />);
      expect(screen.getByText(/failed/i)).toBeVisible();
    });

    it('renders `started`', () => {
      render(<RunStatusTag runId="foo" status="STARTED" />);
      expect(screen.getByText(/running/i)).toBeVisible();
    });
  });
});
