import {Colors, Box, Icon} from '@dagster-io/ui';
import * as React from 'react';

import {AssetKey} from '../types';

import {AutomaterializeRequestedPartitionsLink} from './AutomaterializeRequestedPartitionsLink';
import {CollapsibleSection} from './CollapsibleSection';
import {WaitingOnAssetKeysLink} from './WaitingOnAssetKeysLink';
import {WaitingOnPartitionAssetKeysLink} from './WaitingOnPartitionAssetKeysLink';
import {AutoMateralizeWithConditionFragment} from './types/GetEvaluationsQuery.types';

export type ConditionType = AutoMateralizeWithConditionFragment['__typename'];

interface ConditionProps {
  text: React.ReactNode;
  met: boolean;
  type: 'materialization' | 'skip' | 'discard';
  rightElement?: React.ReactNode;
}

const Condition = ({text, met, type, rightElement}: ConditionProps) => {
  const activeColor = React.useMemo(() => {
    switch (type) {
      case 'skip':
        return Colors.Yellow700;
      case 'discard':
        return Colors.Red700;
      default:
        return Colors.Green700;
    }
  }, [type]);

  return (
    <Box flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
        <Icon name={met ? 'done' : 'close'} color={met ? activeColor : Colors.Gray400} />
        <div style={{color: met ? activeColor : undefined}}>{text}</div>
      </Box>
      {rightElement}
    </Box>
  );
};

interface ConditionsWithPartitionsProps {
  conditionResults: Set<ConditionType>;
  maxMaterializationsPerMinute: number;
  conditionToPartitions: Record<ConditionType, string[]>;
  parentOutdatedWaitingOnAssetKeys: Record<string, AssetKey[]>;
}

export const ConditionsWithPartitions = ({
  conditionResults,
  conditionToPartitions,
  maxMaterializationsPerMinute,
  parentOutdatedWaitingOnAssetKeys,
}: ConditionsWithPartitionsProps) => {
  const buildRightElement = (partitionKeys: string[]) => {
    if (partitionKeys?.length) {
      return <AutomaterializeRequestedPartitionsLink partitionKeys={partitionKeys} />;
    }
    return <div style={{color: Colors.Gray400}}>&ndash;</div>;
  };

  return (
    <>
      <CollapsibleSection header="Materialization conditions met">
        <Box flex={{direction: 'column', gap: 8}}>
          <Condition
            text="Materialization is missing"
            met={conditionResults.has('MissingAutoMaterializeCondition')}
            type="materialization"
            rightElement={buildRightElement(
              conditionToPartitions['MissingAutoMaterializeCondition'],
            )}
          />
          <Condition
            text="Upstream data has changed since latest materialization"
            met={conditionResults.has('ParentMaterializedAutoMaterializeCondition')}
            type="materialization"
            rightElement={buildRightElement(
              conditionToPartitions['ParentMaterializedAutoMaterializeCondition'],
            )}
          />
          <Condition
            text="Required to meet this asset's freshness policy"
            met={conditionResults.has('FreshnessAutoMaterializeCondition')}
            type="materialization"
            rightElement={buildRightElement(
              conditionToPartitions['FreshnessAutoMaterializeCondition'],
            )}
          />
          <Condition
            text="Required to meet a downstream freshness policy"
            met={conditionResults.has('DownstreamFreshnessAutoMaterializeCondition')}
            type="materialization"
            rightElement={buildRightElement(
              conditionToPartitions['DownstreamFreshnessAutoMaterializeCondition'],
            )}
          />
        </Box>
      </CollapsibleSection>
      <CollapsibleSection header="Skip conditions met">
        <Condition
          text="Waiting on upstream data"
          met={conditionResults.has('ParentOutdatedAutoMaterializeCondition')}
          type="skip"
          rightElement={
            Object.keys(parentOutdatedWaitingOnAssetKeys).length > 0 ? (
              <WaitingOnPartitionAssetKeysLink
                assetKeysByPartition={parentOutdatedWaitingOnAssetKeys}
              />
            ) : null
          }
        />
      </CollapsibleSection>
      <CollapsibleSection header="Discard conditions met">
        <Condition
          text={`Exceeds ${
            maxMaterializationsPerMinute === 1
              ? '1 materialization'
              : `${maxMaterializationsPerMinute} materializations`
          } per minute`}
          met={conditionResults.has('MaxMaterializationsExceededAutoMaterializeCondition')}
          type="discard"
          rightElement={buildRightElement(
            conditionToPartitions['MaxMaterializationsExceededAutoMaterializeCondition'],
          )}
        />
      </CollapsibleSection>
    </>
  );
};

interface ConditionsProps {
  conditionResults: Set<ConditionType>;
  maxMaterializationsPerMinute: number;
  parentOutdatedWaitingOnAssetKeys: AssetKey[];
}

export const ConditionsNoPartitions = ({
  conditionResults,
  maxMaterializationsPerMinute,
  parentOutdatedWaitingOnAssetKeys,
}: ConditionsProps) => {
  return (
    <>
      <CollapsibleSection header="Materialization conditions met">
        <Box flex={{direction: 'column', gap: 8}}>
          <Condition
            text="Materialization is missing"
            met={conditionResults.has('MissingAutoMaterializeCondition')}
            type="materialization"
          />
          <Condition
            text="Upstream data has changed since latest materialization"
            met={conditionResults.has('ParentMaterializedAutoMaterializeCondition')}
            type="materialization"
          />
          <Condition
            text="Required to meet this asset's freshness policy"
            met={conditionResults.has('FreshnessAutoMaterializeCondition')}
            type="materialization"
          />
          <Condition
            text="Required to meet a downstream freshness policy"
            met={conditionResults.has('DownstreamFreshnessAutoMaterializeCondition')}
            type="materialization"
          />
        </Box>
      </CollapsibleSection>
      <CollapsibleSection header="Skip conditions met">
        <Condition
          text="Waiting on upstream data"
          met={conditionResults.has('ParentOutdatedAutoMaterializeCondition')}
          type="skip"
          rightElement={
            parentOutdatedWaitingOnAssetKeys.length ? (
              <WaitingOnAssetKeysLink assetKeys={parentOutdatedWaitingOnAssetKeys} />
            ) : null
          }
        />
      </CollapsibleSection>
      <CollapsibleSection header="Discard conditions met">
        <Condition
          text={`Exceeds ${
            maxMaterializationsPerMinute === 1
              ? '1 materialization'
              : `${maxMaterializationsPerMinute} materializations`
          } per minute`}
          met={conditionResults.has('MaxMaterializationsExceededAutoMaterializeCondition')}
          type="discard"
        />
      </CollapsibleSection>
    </>
  );
};
