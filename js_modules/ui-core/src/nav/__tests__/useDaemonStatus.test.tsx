import {MockedProvider} from '@apollo/client/testing';
import {render, renderHook, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {InstigationStatus} from '../../graphql/types';
import {useDaemonStatus} from '../../instance/useDaemonStatus';
import {__resetForJest} from '../../search/useIndexedDBCachedQuery';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {
  buildInstanceWarningQuery,
  buildWorkspaceQueryWithNoSchedulesOrSensors,
  buildWorkspaceQueryWithScheduleAndSensor,
} from '../__fixtures__/useDaemonStatus.fixtures';

afterEach(() => {
  __resetForJest();
});
describe('useDaemonStatus', () => {
  describe('Scheduler daemon', () => {
    it('does not surface scheduler errors if there are no schedules', async () => {
      const daemonHealth = [{daemonType: 'SCHEDULER', healthy: false, required: true}];
      const {result} = renderHook(() => useDaemonStatus(), {
        wrapper: ({children}: {children: React.ReactNode}) => (
          <MockedProvider
            mocks={[
              ...buildWorkspaceQueryWithNoSchedulesOrSensors(),
              buildInstanceWarningQuery(daemonHealth),
            ]}
          >
            <WorkspaceProvider>{children}</WorkspaceProvider>
          </MockedProvider>
        ),
      });

      expect(result.current).toBeNull();
    });

    it('does not surface scheduler errors if there are no running schedules', async () => {
      const daemonHealth = [{daemonType: 'SCHEDULER', healthy: false, required: true}];

      const {result} = renderHook(() => useDaemonStatus(), {
        wrapper: ({children}: {children: React.ReactNode}) => (
          <MockedProvider
            mocks={[
              ...buildWorkspaceQueryWithScheduleAndSensor({
                schedule: InstigationStatus.STOPPED,
                sensor: InstigationStatus.RUNNING,
              }),
              buildInstanceWarningQuery(daemonHealth),
            ]}
          >
            <WorkspaceProvider>{children}</WorkspaceProvider>
          </MockedProvider>
        ),
      });

      expect(result.current).toBeNull();
    });

    it('does surface scheduler errors if there is a running schedule', async () => {
      const daemonHealth = [{daemonType: 'SCHEDULER', healthy: false, required: true}];

      const {result} = renderHook(() => useDaemonStatus(), {
        wrapper: ({children}: {children: React.ReactNode}) => (
          <MockedProvider
            mocks={[
              ...buildWorkspaceQueryWithScheduleAndSensor({
                schedule: InstigationStatus.RUNNING,
                sensor: InstigationStatus.RUNNING,
              }),
              buildInstanceWarningQuery(daemonHealth),
            ]}
          >
            <WorkspaceProvider>{children}</WorkspaceProvider>
          </MockedProvider>
        ),
      });

      await waitFor(() => {
        expect(result.current?.type).toBe('warning');
        render(<div>{result.current?.content}</div>);
        expect(screen.getByText(/1 daemon not running/i)).toBeVisible();
      });
    });
  });

  describe('Sensor daemon', () => {
    it('does not surface sensor daemon errors if there are no sensors', async () => {
      const daemonHealth = [{daemonType: 'SENSOR', healthy: false, required: true}];

      const {result} = renderHook(() => useDaemonStatus(), {
        wrapper: ({children}: {children: React.ReactNode}) => (
          <MockedProvider
            mocks={[
              ...buildWorkspaceQueryWithNoSchedulesOrSensors(),
              buildInstanceWarningQuery(daemonHealth),
            ]}
          >
            <WorkspaceProvider>{children}</WorkspaceProvider>
          </MockedProvider>
        ),
      });

      expect(result.current).toBeNull();
    });

    it('does not surface sensor daemon errors if there are no running sensors', async () => {
      const daemonHealth = [{daemonType: 'SENSOR', healthy: false, required: true}];

      const {result} = renderHook(() => useDaemonStatus(), {
        wrapper: ({children}: {children: React.ReactNode}) => (
          <MockedProvider
            mocks={[
              ...buildWorkspaceQueryWithScheduleAndSensor({
                schedule: InstigationStatus.RUNNING,
                sensor: InstigationStatus.STOPPED,
              }),
              buildInstanceWarningQuery(daemonHealth),
            ]}
          >
            <WorkspaceProvider>{children}</WorkspaceProvider>
          </MockedProvider>
        ),
      });

      expect(result.current).toBeNull();
    });

    it('does surface sensor daemon errors if there is a running sensor', async () => {
      const daemonHealth = [{daemonType: 'SENSOR', healthy: false, required: true}];

      const {result} = renderHook(() => useDaemonStatus(), {
        wrapper: ({children}: {children: React.ReactNode}) => (
          <MockedProvider
            mocks={[
              ...buildWorkspaceQueryWithScheduleAndSensor({
                schedule: InstigationStatus.RUNNING,
                sensor: InstigationStatus.RUNNING,
              }),
              buildInstanceWarningQuery(daemonHealth),
            ]}
          >
            <WorkspaceProvider>{children}</WorkspaceProvider>
          </MockedProvider>
        ),
      });

      await waitFor(() => {
        expect(result.current?.type).toBe('warning');
        render(<div>{result.current?.content}</div>);
        expect(screen.getByText(/1 daemon not running/i)).toBeVisible();
      });
    });
  });

  describe('Backfill daemon', () => {
    it('does not surface backfill daemon errors if there are no backfills', async () => {
      const daemonHealth = [{daemonType: 'BACKFILL', healthy: false, required: true}];

      const {result} = renderHook(() => useDaemonStatus(), {
        wrapper: ({children}: {children: React.ReactNode}) => (
          <MockedProvider
            mocks={[
              ...buildWorkspaceQueryWithNoSchedulesOrSensors(),
              buildInstanceWarningQuery(daemonHealth),
            ]}
          >
            <WorkspaceProvider>{children}</WorkspaceProvider>
          </MockedProvider>
        ),
      });

      expect(result.current).toBeNull();
    });

    it('does surface backfill daemon errors if there is a backfill', async () => {
      const daemonHealth = [{daemonType: 'BACKFILL', healthy: false, required: true}];

      const {result} = renderHook(() => useDaemonStatus(), {
        wrapper: ({children}: {children: React.ReactNode}) => (
          <MockedProvider
            mocks={[
              ...buildWorkspaceQueryWithNoSchedulesOrSensors(),
              buildInstanceWarningQuery(daemonHealth, 1),
            ]}
          >
            <WorkspaceProvider>{children}</WorkspaceProvider>
          </MockedProvider>
        ),
      });

      await waitFor(() => {
        expect(result.current?.type).toBe('warning');
        render(<div>{result.current?.content}</div>);
        expect(screen.getByText(/1 daemon not running/i)).toBeVisible();
      });
    });
  });

  describe('Multiple daemons', () => {
    it('surfaces multiple errors', async () => {
      const daemonHealth = [
        {daemonType: 'SCHEDULER', healthy: false, required: true},
        {daemonType: 'SENSOR', healthy: false, required: true},
        {daemonType: 'BACKFILL', healthy: false, required: true},
      ];

      const {result} = renderHook(() => useDaemonStatus(), {
        wrapper: ({children}: {children: React.ReactNode}) => (
          <MockedProvider
            mocks={[
              ...buildWorkspaceQueryWithScheduleAndSensor({
                schedule: InstigationStatus.RUNNING,
                sensor: InstigationStatus.RUNNING,
              }),
              buildInstanceWarningQuery(daemonHealth, 1),
            ]}
          >
            <WorkspaceProvider>{children}</WorkspaceProvider>
          </MockedProvider>
        ),
      });

      await waitFor(() => {
        expect(result.current?.type).toBe('warning');
        render(<div>{result.current?.content}</div>);
        expect(screen.getByText(/3 daemons not running/i)).toBeVisible();
      });
    });
  });
});
