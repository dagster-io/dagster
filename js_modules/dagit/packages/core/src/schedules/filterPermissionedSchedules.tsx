import {InstigationStatus} from '../graphql/types';
import {BasicInstigationStateFragment} from '../overview/types/BasicInstigationStateFragment.types';

export const filterPermissionedSchedules = (schedule: {
  scheduleState: BasicInstigationStateFragment;
}) => {
  const {scheduleState} = schedule;
  return (
    (scheduleState.hasStartPermission && scheduleState.status === InstigationStatus.STOPPED) ||
    (scheduleState.hasStopPermission && scheduleState.status === InstigationStatus.RUNNING)
  );
};
