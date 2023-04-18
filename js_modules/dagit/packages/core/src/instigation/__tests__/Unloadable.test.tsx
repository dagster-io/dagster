import {MockedProvider} from '@apollo/client/testing';
import {render, screen} from '@testing-library/react';
import * as React from 'react';

import {InstigationStatus} from '../../graphql/types';
import {UnloadableSensors} from '../Unloadable';
import {unloadableSchedule, unloadableSensor} from '../__fixtures__/Unloadable.fixtures';

describe('Unloadables', () => {
  describe('Sensors', () => {
    it('shows enabled ON switch if running and viewer has permission to edit sensors', async () => {
      render(
        <MockedProvider>
          <UnloadableSensors sensorStates={[unloadableSensor]} />
        </MockedProvider>,
      );

      const switchElem: HTMLInputElement = screen.getByRole('checkbox');
      expect(switchElem.checked).toBe(true);
      expect(switchElem.disabled).toBe(false);
    });

    it('shows disabled OFF switch if stopped, even if viewer has permission to edit sensors', async () => {
      render(
        <MockedProvider>
          <UnloadableSensors
            sensorStates={[{...unloadableSensor, status: InstigationStatus.STOPPED}]}
          />
        </MockedProvider>,
      );

      const switchElem: HTMLInputElement = screen.getByRole('checkbox');
      expect(switchElem.checked).toBe(false);
      expect(switchElem.disabled).toBe(true);
    });

    it('shows disabled ON switch if running and no permission to edit sensors', async () => {
      render(
        <MockedProvider>
          <UnloadableSensors sensorStates={[{...unloadableSensor, hasStopPermission: false}]} />
        </MockedProvider>,
      );

      const switchElem: HTMLInputElement = screen.getByRole('checkbox');
      expect(switchElem.checked).toBe(true);
      expect(switchElem.disabled).toBe(true);
    });

    it('shows disabled OFF switch if stopped and no permission to edit sensors', async () => {
      render(
        <MockedProvider>
          <UnloadableSensors
            sensorStates={[
              {...unloadableSensor, status: InstigationStatus.STOPPED, hasStopPermission: false},
            ]}
          />
        </MockedProvider>,
      );

      const switchElem: HTMLInputElement = screen.getByRole('checkbox');
      expect(switchElem.checked).toBe(false);
      expect(switchElem.disabled).toBe(true);
    });
  });

  describe('Schedules', () => {
    it('shows enabled ON switch if running and viewer has permission to stop schedules', async () => {
      render(
        <MockedProvider>
          <UnloadableSensors sensorStates={[unloadableSchedule]} />
        </MockedProvider>,
      );

      const switchElem: HTMLInputElement = screen.getByRole('checkbox');
      expect(switchElem.checked).toBe(true);
      expect(switchElem.disabled).toBe(false);
    });

    it('shows disabled OFF switch if stopped, even if viewer has permission to start schedule', async () => {
      render(
        <MockedProvider>
          <UnloadableSensors
            sensorStates={[{...unloadableSchedule, status: InstigationStatus.STOPPED}]}
          />
        </MockedProvider>,
      );

      const switchElem: HTMLInputElement = screen.getByRole('checkbox');
      expect(switchElem.checked).toBe(false);
      expect(switchElem.disabled).toBe(true);
    });

    it('shows disabled ON switch if running and no permission to stop schedules', async () => {
      render(
        <MockedProvider>
          <UnloadableSensors sensorStates={[{...unloadableSchedule, hasStopPermission: false}]} />
        </MockedProvider>,
      );

      const switchElem: HTMLInputElement = screen.getByRole('checkbox');
      expect(switchElem.checked).toBe(true);
      expect(switchElem.disabled).toBe(true);
    });

    it('shows disabled OFF switch if stopped and no permission to start schedule', async () => {
      render(
        <MockedProvider>
          <UnloadableSensors
            sensorStates={[
              {...unloadableSchedule, status: InstigationStatus.STOPPED, hasStartPermission: false},
            ]}
          />
        </MockedProvider>,
      );

      const switchElem: HTMLInputElement = screen.getByRole('checkbox');
      expect(switchElem.checked).toBe(false);
      expect(switchElem.disabled).toBe(true);
    });
  });
});
