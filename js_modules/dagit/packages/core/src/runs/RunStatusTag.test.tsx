import {render, screen} from '@testing-library/react';
import React from 'react';

import {RunStatus} from '../types/globalTypes';

import {RunStatusTag} from './RunStatusTag';

describe('RunStatusTag', () => {
  describe('Status type', () => {
    it('renders `succeeded`', () => {
      render(<RunStatusTag status={RunStatus.SUCCESS} />);
      expect(screen.getByText(/success/i)).toBeVisible();
    });

    it('renders `failed`', () => {
      render(<RunStatusTag status={RunStatus.FAILURE} />);
      expect(screen.getByText(/failure/i)).toBeVisible();
    });

    it('renders `started`', () => {
      render(<RunStatusTag status={RunStatus.STARTED} />);
      expect(screen.getByText(/started/i)).toBeVisible();
    });
  });
});
