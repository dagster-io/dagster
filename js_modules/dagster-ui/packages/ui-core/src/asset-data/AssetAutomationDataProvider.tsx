import {ApolloClient, gql, useApolloClient} from '../apollo-client';
import {tokenForAssetKey, tokenToAssetKey} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';
import {liveDataFactory} from '../live-data-provider/Factory';
import {LiveDataThreadID} from '../live-data-provider/LiveDataThread';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
import {
  AssetAutomationFragment,
  AssetAutomationQuery,
  AssetAutomationQueryVariables,
} from './types/AssetAutomationDataProvider.types';
import {SCHEDULE_SWITCH_FRAGMENT} from '../schedules/ScheduleSwitchFragment';
import {SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitchFragment';
import {weakMapMemoize} from '../util/weakMapMemoize';

function init() {
  return liveDataFactory(
    () => {
      return useApolloClient();
    },
    async (keys, client: ApolloClient<any>) => {
      const assetKeys = keys.map(tokenToAssetKey);

      const {data} = await client.query<AssetAutomationQuery, AssetAutomationQueryVariables>({
        query: ASSETS_INSTIGATOR_QUERY,
        fetchPolicy: 'no-cache',
        variables: {
          assetKeys,
        },
      });

      const result: Record<string, AssetAutomationFragment> = Object.fromEntries(
        data.assetNodes.map((node) => [tokenForAssetKey(node.assetKey), node]),
      );

      // External assets are not included in the response, so provide a blank state assetInstigator
      keys.forEach((key) => {
        if (!result[key]) {
          result[key] = {
            __typename: 'AssetNode',
            id: key,
            assetKey: {
              __typename: 'AssetKey',
              ...tokenToAssetKey(key),
            },
            automationCondition: null,
            targetingInstigators: [],
            lastAutoMaterializationEvaluationRecord: null,
          };
        }
      });
      return result;
    },
  );
}

export const AssetAutomationData = init();

export function useAssetAutomationData(
  assetKey: AssetKeyInput,
  thread: LiveDataThreadID = 'default',
) {
  const result = AssetAutomationData.useLiveDataSingle(tokenForAssetKey(assetKey), thread);
  useBlockTraceUntilTrue('useAssetAutomationData', !!result.liveData);
  return result;
}

const memoizedAssetKeys = weakMapMemoize((assetKeys: AssetKeyInput[]) => {
  return assetKeys.map((key) => tokenForAssetKey(key));
});

export function useAssetsAutomationData(
  assetKeys: AssetKeyInput[],
  thread: LiveDataThreadID = 'AssetAutomation', // Use AssetAutomation to get 250 batch size
) {
  const keys = memoizedAssetKeys(assetKeys);
  const result = AssetAutomationData.useLiveData(keys, thread);
  useBlockTraceUntilTrue(
    'useAssetsAutomationData',
    !!(Object.keys(result.liveDataByNode).length === assetKeys.length),
  );
  return result;
}

export const ASSETS_INSTIGATOR_QUERY = gql`
  query AssetAutomationQuery($assetKeys: [AssetKeyInput!]!) {
    assetNodes(assetKeys: $assetKeys) {
      id
      ...AssetAutomationFragment
    }
  }

  fragment AssetAutomationFragment on AssetNode {
    id
    assetKey {
      path
    }
    automationCondition {
      label
      expandedLabel
    }
    targetingInstigators {
      ...AssetInstigatorFragment
    }
    lastAutoMaterializationEvaluationRecord {
      id
      evaluationId
    }
  }

  fragment AssetInstigatorFragment on Instigator {
    ... on Schedule {
      ...ScheduleSwitchFragment
    }
    ... on Sensor {
      ...SensorSwitchFragment
    }
  }

  ${SENSOR_SWITCH_FRAGMENT}
  ${SCHEDULE_SWITCH_FRAGMENT}
`;

// For tests
export function __resetForJest() {
  Object.assign(AssetAutomationData, init());
}
