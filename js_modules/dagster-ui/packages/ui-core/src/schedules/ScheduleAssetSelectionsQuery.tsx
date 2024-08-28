import {gql} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {AUTOMATION_ASSET_SELECTION_FRAGMENT} from '../automation/AutomationAssetSelectionFragment';

export const SCHEDULE_ASSET_SELECTIONS_QUERY = gql`
  query ScheduleAssetSelectionQuery($scheduleSelector: ScheduleSelector!) {
    scheduleOrError(scheduleSelector: $scheduleSelector) {
      ... on Schedule {
        id
        assetSelection {
          ...AutomationAssetSelectionFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${AUTOMATION_ASSET_SELECTION_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
