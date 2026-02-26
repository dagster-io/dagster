import {InstigationStatus, InstigationType, buildInstigationState} from '../../graphql/types';

export const unloadableSchedule = buildInstigationState({
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
});

export const unloadableSensor = buildInstigationState({
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
});
