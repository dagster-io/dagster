import {gql, useQuery} from '@apollo/client';
import {act, render, screen} from '@testing-library/react';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {TestProvider} from '../testing/TestProvider';
import {InstigationStatus} from '../types/globalTypes';

import {INSTIGATION_STATE_FRAGMENT} from './InstigationUtils';
import {UnloadableSchedules, UnloadableSensors} from './Unloadable';
import {UnloadableInstigationStatesQuery} from './types/UnloadableInstigationStatesQuery';

describe('Unloadables', () => {
  const UNLOADABLE_INSTIGATION_STATES_QUERY = gql`
    query UnloadableInstigationStatesQuery {
      unloadableInstigationStatesOrError {
        ... on InstigationStates {
          results {
            id
            ...InstigationStateFragment
          }
        }
        ...PythonErrorFragment
      }
    }

    ${PYTHON_ERROR_FRAGMENT}
    ${INSTIGATION_STATE_FRAGMENT}
  `;

  const defaultMocks = {
    InstigationStates: () => ({
      results: () => [...new Array(1)],
    }),
  };

  describe('Sensors', () => {
    const Test = () => {
      const {data, loading} = useQuery<UnloadableInstigationStatesQuery>(
        UNLOADABLE_INSTIGATION_STATES_QUERY,
      );
      if (loading) {
        return <div>Loading…</div>;
      }
      const states = data?.unloadableInstigationStatesOrError;
      if (states && states.__typename === 'InstigationStates') {
        return <UnloadableSensors sensorStates={states.results} />;
      }
      return <div>Error!</div>;
    };

    it('shows enabled ON switch if running and viewer has permission to edit sensors', async () => {
      const mocks = {
        InstigationState: () => ({
          status: () => InstigationStatus.RUNNING,
        }),
      };

      await act(async () => {
        render(
          <TestProvider
            apolloProps={{mocks: [defaultMocks, mocks]}}
            permissionOverrides={{edit_sensor: {enabled: true, disabledReason: null}}}
          >
            <Test />
          </TestProvider>,
        );
      });

      const switchElem: HTMLInputElement = screen.getByRole('checkbox');
      expect(switchElem.checked).toBe(true);
      expect(switchElem.disabled).toBe(false);
    });

    it('shows disabled OFF switch if stopped, even if viewer has permission to edit sensors', async () => {
      const mocks = {
        InstigationState: () => ({
          status: () => InstigationStatus.STOPPED,
        }),
      };

      await act(async () => {
        render(
          <TestProvider
            apolloProps={{mocks: [defaultMocks, mocks]}}
            permissionOverrides={{edit_sensor: {enabled: true, disabledReason: null}}}
          >
            <Test />
          </TestProvider>,
        );
      });

      const switchElem: HTMLInputElement = screen.getByRole('checkbox');
      expect(switchElem.checked).toBe(false);
      expect(switchElem.disabled).toBe(true);
    });

    it('shows disabled ON switch if running and no permission to edit sensors', async () => {
      const mocks = {
        InstigationState: () => ({
          status: () => InstigationStatus.RUNNING,
        }),
      };

      await act(async () => {
        render(
          <TestProvider
            apolloProps={{mocks: [defaultMocks, mocks]}}
            permissionOverrides={{edit_sensor: {enabled: false, disabledReason: 'Nope'}}}
          >
            <Test />
          </TestProvider>,
        );
      });

      const switchElem: HTMLInputElement = screen.getByRole('checkbox');
      expect(switchElem.checked).toBe(true);
      expect(switchElem.disabled).toBe(true);
    });

    it('shows disabled OFF switch if stopped and no permission to edit sensors', async () => {
      const mocks = {
        InstigationState: () => ({
          status: () => InstigationStatus.STOPPED,
        }),
      };

      await act(async () => {
        render(
          <TestProvider
            apolloProps={{mocks: [defaultMocks, mocks]}}
            permissionOverrides={{edit_sensor: {enabled: false, disabledReason: 'Nope'}}}
          >
            <Test />
          </TestProvider>,
        );
      });

      const switchElem: HTMLInputElement = screen.getByRole('checkbox');
      expect(switchElem.checked).toBe(false);
      expect(switchElem.disabled).toBe(true);
    });
  });

  describe('Schedules', () => {
    const Test = () => {
      const {data, loading} = useQuery<UnloadableInstigationStatesQuery>(
        UNLOADABLE_INSTIGATION_STATES_QUERY,
      );
      if (loading) {
        return <div>Loading…</div>;
      }
      const states = data?.unloadableInstigationStatesOrError;
      if (states && states.__typename === 'InstigationStates') {
        return <UnloadableSchedules scheduleStates={states.results} />;
      }
      return <div>Error!</div>;
    };

    it('shows enabled ON switch if running and viewer has permission to stop schedules', async () => {
      const mocks = {
        InstigationState: () => ({
          status: () => InstigationStatus.RUNNING,
        }),
      };

      await act(async () => {
        render(
          <TestProvider
            apolloProps={{mocks: [defaultMocks, mocks]}}
            permissionOverrides={{stop_running_schedule: {enabled: true, disabledReason: null}}}
          >
            <Test />
          </TestProvider>,
        );
      });

      const switchElem: HTMLInputElement = screen.getByRole('checkbox');
      expect(switchElem.checked).toBe(true);
      expect(switchElem.disabled).toBe(false);
    });

    it('shows disabled OFF switch if stopped, even if viewer has permission to start schedule', async () => {
      const mocks = {
        InstigationState: () => ({
          status: () => InstigationStatus.STOPPED,
        }),
      };

      await act(async () => {
        render(
          <TestProvider
            apolloProps={{mocks: [defaultMocks, mocks]}}
            permissionOverrides={{start_schedule: {enabled: true, disabledReason: null}}}
          >
            <Test />
          </TestProvider>,
        );
      });

      const switchElem: HTMLInputElement = screen.getByRole('checkbox');
      expect(switchElem.checked).toBe(false);
      expect(switchElem.disabled).toBe(true);
    });

    it('shows disabled ON switch if running and no permission to stop schedules', async () => {
      const mocks = {
        InstigationState: () => ({
          status: () => InstigationStatus.RUNNING,
        }),
      };

      await act(async () => {
        render(
          <TestProvider
            apolloProps={{mocks: [defaultMocks, mocks]}}
            permissionOverrides={{stop_running_schedule: {enabled: false, disabledReason: 'nope'}}}
          >
            <Test />
          </TestProvider>,
        );
      });

      const switchElem: HTMLInputElement = screen.getByRole('checkbox');
      expect(switchElem.checked).toBe(true);
      expect(switchElem.disabled).toBe(true);
    });

    it('shows disabled OFF switch if stopped and no permission to start schedule', async () => {
      const mocks = {
        InstigationState: () => ({
          status: () => InstigationStatus.STOPPED,
        }),
      };

      await act(async () => {
        render(
          <TestProvider
            apolloProps={{mocks: [defaultMocks, mocks]}}
            permissionOverrides={{start_schedule: {enabled: false, disabledReason: 'nope'}}}
          >
            <Test />
          </TestProvider>,
        );
      });

      const switchElem: HTMLInputElement = screen.getByRole('checkbox');
      expect(switchElem.checked).toBe(false);
      expect(switchElem.disabled).toBe(true);
    });
  });
});
