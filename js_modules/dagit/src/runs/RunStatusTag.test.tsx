import {render, screen} from '@testing-library/react';
import React from 'react';

import {RunStatusTag} from 'src/runs/RunStatusTag';

describe('RunStatusTag', () => {
  describe('Status type', () => {
    it('renders `succeeded`', () => {
      render(<RunStatusTag status="SUCCESS" />);
      expect(screen.getByText(/succeeded/i)).toBeVisible();
    });

    it('renders `failed`', () => {
      render(<RunStatusTag status="FAILURE" />);
      expect(screen.getByText(/failed/i)).toBeVisible();
    });

    it('renders `started`', () => {
      render(<RunStatusTag status="STARTED" />);
      expect(screen.getByText(/running/i)).toBeVisible();
    });
  });
});
