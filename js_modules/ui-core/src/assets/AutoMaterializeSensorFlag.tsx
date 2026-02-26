import {gql, useQuery} from '../apollo-client';
import {
  AutoMaterializeSensorFlagQuery,
  AutoMaterializeSensorFlagQueryVariables,
} from './types/AutoMaterializeSensorFlag.types';

type FlagState = 'unknown' | 'has-sensor-amp' | 'has-global-amp';

export const useAutoMaterializeSensorFlag = (): FlagState => {
  const queryResult = useQuery<
    AutoMaterializeSensorFlagQuery,
    AutoMaterializeSensorFlagQueryVariables
  >(AUTO_MATERIALIZE_POLICY_SENSOR_FLAG_QUERY);
  const {data} = queryResult;
  if (!data) {
    return 'unknown';
  }
  return data?.instance.useAutoMaterializeSensors ? 'has-sensor-amp' : 'has-global-amp';
};

export const AUTO_MATERIALIZE_POLICY_SENSOR_FLAG_QUERY = gql`
  query AutoMaterializeSensorFlag {
    instance {
      id
      useAutoMaterializeSensors
    }
  }
`;
