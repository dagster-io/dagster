import {InstigationStatus} from '../graphql/types';
import {BasicInstigationStateFragment} from '../overview/types/BasicInstigationStateFragment.types';

export const filterPermissionedInstigationState = (
  instigationState: BasicInstigationStateFragment,
) => {
  return (
    (instigationState.hasStartPermission &&
      instigationState.status === InstigationStatus.STOPPED) ||
    (instigationState.hasStopPermission && instigationState.status === InstigationStatus.RUNNING)
  );
};
