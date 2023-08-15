import {InstigationStatus, InstigationType} from '../../graphql/types';
import {InstigationStateFragment} from '../types/InstigationUtils.types';

export const unloadableSchedule: InstigationStateFragment = {
  __typename: 'InstigationState',
  id: 'my-schedule',
  selectorId: '',
  name: 'my-schedule',
  instigationType: InstigationType.SCHEDULE,
  status: InstigationStatus.RUNNING,
  hasStartPermission: true,
  hasStopPermission: true,
  repositoryName: 'some-repo',
  repositoryLocationName: 'some-location',
  runningCount: 1,
  typeSpecificData: null,
  runs: [],
  ticks: [],
};

export const unloadableSensor: InstigationStateFragment = {
  __typename: 'InstigationState',
  id: 'my-sensor',
  selectorId: '',
  name: 'my-sensor',
  instigationType: InstigationType.SENSOR,
  status: InstigationStatus.RUNNING,
  hasStartPermission: true,
  hasStopPermission: true,
  repositoryName: 'some-repo',
  repositoryLocationName: 'some-location',
  runningCount: 1,
  typeSpecificData: null,
  runs: [],
  ticks: [],
};
