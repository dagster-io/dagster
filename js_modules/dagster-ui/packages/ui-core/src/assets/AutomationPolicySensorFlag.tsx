import {gql, useQuery} from '@apollo/client';

import {
  AutomationPolicySensorFlagQuery,
  AutomationPolicySensorFlagQueryVariables,
} from './types/AutomationPolicySensorFlag.types';

type FlagState = 'unknown' | 'has-sensor-amp' | 'has-global-amp';

export const useAutomationPolicySensorFlag = (): FlagState => {
  const {data} = useQuery<
    AutomationPolicySensorFlagQuery,
    AutomationPolicySensorFlagQueryVariables
  >(AUTOMATION_POLICY_SENSOR_FLAG);
  if (!data) {
    return 'unknown';
  }
  return data?.instance.useAutomationPolicySensors ? 'has-sensor-amp' : 'has-global-amp';
};

const AUTOMATION_POLICY_SENSOR_FLAG = gql`
  query AutomationPolicySensorFlag {
    instance {
      id
      useAutomationPolicySensors
    }
  }
`;
