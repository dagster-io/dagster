import {Colors, Box, Icon, Tag} from '@dagster-io/ui';
import * as React from 'react';

import {AssetKey} from '../types';

import {AutomaterializeRequestedPartitionsLink} from './AutomaterializeRequestedPartitionsLink';
import {CollapsibleSection} from './CollapsibleSection';
import {ParentUpdatedLink} from './ParentUpdatedLink';
import {ParentUpdatedPartitionLink} from './ParentUpdatedPartitionLink';
import {WaitingOnAssetKeysLink} from './WaitingOnAssetKeysLink';
import {WaitingOnPartitionAssetKeysLink} from './WaitingOnPartitionAssetKeysLink';
import {AutoMateralizeWithConditionFragment} from './types/GetEvaluationsQuery.types';

export type ConditionType = AutoMateralizeWithConditionFragment['__typename'];

interface ConditionProps {
  text: React.ReactNode;
  met: boolean;
  rightElement?: React.ReactNode;
}

const Condition = ({text, met, rightElement}: ConditionProps) => {
  return (
    <Box
      flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
      style={{height: 24}}
    >
      <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
        <Icon name={met ? 'done' : 'close'} color={met ? Colors.Dark : Colors.Gray500} />
        <div style={{color: met ? Colors.Dark : Colors.Gray500}}>{text}</div>
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
  parentUpdatedAssetKeys: Record<string, AssetKey[]>;
  parentWillUpdateAssetKeys: Record<string, AssetKey[]>;
}

export const ConditionsWithPartitions = ({
  conditionResults,
  conditionToPartitions,
  maxMaterializationsPerMinute,
  parentOutdatedWaitingOnAssetKeys,
  parentUpdatedAssetKeys,
  parentWillUpdateAssetKeys,
}: ConditionsWithPartitionsProps) => {
  const buildRightElement = (
    partitionKeys: string[],
    intent?: React.ComponentProps<typeof Tag>['intent'],
  ) => {
    if (partitionKeys?.length) {
      return (
        <AutomaterializeRequestedPartitionsLink partitionKeys={partitionKeys} intent={intent} />
      );
    }
    return <div style={{color: Colors.Gray400}}>&ndash;</div>;
  };

  return (
    <>
      <CollapsibleSection
        header="Materialization conditions met"
        details="These conditions trigger materializations, unless they are overriden by a skip or discard condition."
      >
        <Box flex={{direction: 'column', gap: 8}}>
          <Condition
            text="Materialization is missing"
            met={conditionResults.has('MissingAutoMaterializeCondition')}
            rightElement={buildRightElement(
              conditionToPartitions['MissingAutoMaterializeCondition'],
            )}
          />
          <Condition
            text="Upstream data has changed since latest materialization"
            met={conditionResults.has('ParentMaterializedAutoMaterializeCondition')}
            rightElement={
              Object.keys(parentUpdatedAssetKeys).length +
                Object.keys(parentWillUpdateAssetKeys).length >
              0 ? (
                <ParentUpdatedPartitionLink
                  updatedAssetKeys={parentUpdatedAssetKeys}
                  willUpdateAssetKeys={parentWillUpdateAssetKeys}
                />
              ) : null
            }
          />
          <Condition
            text="Required to meet this asset's freshness policy"
            met={conditionResults.has('FreshnessAutoMaterializeCondition')}
            rightElement={buildRightElement(
              conditionToPartitions['FreshnessAutoMaterializeCondition'],
            )}
          />
          <Condition
            text="Required to meet a downstream freshness policy"
            met={conditionResults.has('DownstreamFreshnessAutoMaterializeCondition')}
            rightElement={buildRightElement(
              conditionToPartitions['DownstreamFreshnessAutoMaterializeCondition'],
            )}
          />
        </Box>
      </CollapsibleSection>
      <CollapsibleSection
        header="Skip conditions met"
        details="Skipped partitions will be materialized in a future evaluation, once the skip condition is resolved."
      >
        <Condition
          text="Waiting on upstream data"
          met={conditionResults.has('ParentOutdatedAutoMaterializeCondition')}
          rightElement={
            Object.keys(parentOutdatedWaitingOnAssetKeys).length > 0 ? (
              <WaitingOnPartitionAssetKeysLink
                assetKeysByPartition={parentOutdatedWaitingOnAssetKeys}
              />
            ) : null
          }
        />
      </CollapsibleSection>
      <CollapsibleSection
        header="Discard conditions met"
        details="Discarded partitions will not be materialized unless new materialization conditions occur. You may want to run a manual backfill to respond to the materialize conditions."
      >
        <Condition
          text={`Exceeds ${
            maxMaterializationsPerMinute === 1
              ? '1 materialization'
              : `${maxMaterializationsPerMinute} materializations`
          } per minute`}
          met={conditionResults.has('MaxMaterializationsExceededAutoMaterializeCondition')}
          rightElement={buildRightElement(
            conditionToPartitions['MaxMaterializationsExceededAutoMaterializeCondition'],
            'danger',
          )}
        />
      </CollapsibleSection>
    </>
  );
};

interface ConditionsProps {
  conditionResults: Set<ConditionType>;
  parentOutdatedWaitingOnAssetKeys: AssetKey[];
  parentUpdatedAssetKeys: AssetKey[];
  parentWillUpdateAssetKeys: AssetKey[];
}

export const ConditionsNoPartitions = ({
  conditionResults,
  parentOutdatedWaitingOnAssetKeys,
  parentUpdatedAssetKeys,
  parentWillUpdateAssetKeys,
}: ConditionsProps) => {
  return (
    <>
      <CollapsibleSection
        header="Materialization conditions met"
        details="These conditions trigger a materialization, unless they are blocked by a skip or discard condition."
      >
        <Box flex={{direction: 'column', gap: 8}}>
          <Condition
            text="Materialization is missing"
            met={conditionResults.has('MissingAutoMaterializeCondition')}
          />
          <Condition
            text="Upstream data has changed since latest materialization"
            met={conditionResults.has('ParentMaterializedAutoMaterializeCondition')}
            rightElement={
              parentUpdatedAssetKeys.length + parentWillUpdateAssetKeys.length ? (
                <ParentUpdatedLink
                  updatedAssetKeys={parentUpdatedAssetKeys}
                  willUpdateAssetKeys={parentWillUpdateAssetKeys}
                />
              ) : null
            }
          />
          <Condition
            text="Required to meet this asset's freshness policy"
            met={conditionResults.has('FreshnessAutoMaterializeCondition')}
          />
          <Condition
            text="Required to meet a downstream freshness policy"
            met={conditionResults.has('DownstreamFreshnessAutoMaterializeCondition')}
          />
        </Box>
      </CollapsibleSection>
      <CollapsibleSection
        header="Skip conditions met"
        details="Skips will materialize in a future evaluation, once the skip condition is resolved."
      >
        <Condition
          text="Waiting on upstream data"
          met={conditionResults.has('ParentOutdatedAutoMaterializeCondition')}
          rightElement={
            parentOutdatedWaitingOnAssetKeys.length ? (
              <WaitingOnAssetKeysLink assetKeys={parentOutdatedWaitingOnAssetKeys} />
            ) : null
          }
        />
      </CollapsibleSection>
    </>
  );
};
