import {InstigationStatus} from '../graphql/types';
import {BasicInstigationStateFragment} from '../overview/types/BasicInstigationStateFragment.types';

export const instigationStateSummary = (instigationStates: BasicInstigationStateFragment[]) => {
  let anyOff = false;
  let anyOn = false;

  for (const state of instigationStates) {
    const {status} = state;
    if (status === InstigationStatus.RUNNING) {
      anyOn = true;
    } else if (status === InstigationStatus.STOPPED) {
      anyOff = true;
    }
    if (anyOn && anyOff) {
      break;
    }
  }

  return {anyOff, anyOn};
};
