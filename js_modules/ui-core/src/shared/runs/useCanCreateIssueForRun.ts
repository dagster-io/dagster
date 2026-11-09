import {RunStatus} from '../../graphql/types';

export const useCanCreateIssueForRun = (_runStatus: RunStatus) => ({
  visible: false,
  enabled: false,
  disabledReason: '',
});
