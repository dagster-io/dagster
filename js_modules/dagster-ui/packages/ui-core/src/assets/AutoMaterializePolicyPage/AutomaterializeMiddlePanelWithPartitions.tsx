import {Box, Colors, Subheading} from '@dagster-io/ui-components';
import * as React from 'react';

import {AssetKey} from '../types';

import {AutomaterializeRequestedPartitionsLink} from './AutomaterializeRequestedPartitionsLink';
import {ConditionType, ConditionsWithPartitions} from './Conditions';
import {EvaluationOrEmpty} from './types';
import {RuleWithEvaluationsFragment} from './types/GetEvaluationsQuery.types';

const isRequestCondition = (
  condition: RuleWithEvaluationsFragment,
): condition is RuleWithEvaluationsFragment => {
  switch (condition.__typename) {
    case 'MissingAutoMaterializeCondition':
    case 'DownstreamFreshnessAutoMaterializeCondition':
    case 'FreshnessAutoMaterializeCondition':
    case 'ParentMaterializedAutoMaterializeCondition':
      return true;
    default:
      return false;
  }
};

const extractRequestedPartitionKeys = (conditions: RuleWithEvaluationsFragment[]) => {
  let requested: string[] = [];
  let skippedOrDiscarded: string[] = [];

  conditions.forEach((condition) => {
    const didRequest = isRequestCondition(condition);
    const partitionKeys =
      condition.partitionKeysOrError?.__typename === 'PartitionKeys'
        ? condition.partitionKeysOrError.partitionKeys
        : [];
    if (didRequest) {
      requested = requested.concat(partitionKeys);
    } else {
      skippedOrDiscarded = skippedOrDiscarded.concat(partitionKeys);
    }
  });

  const skippedOrDiscardedSet = new Set(skippedOrDiscarded);
  return new Set(requested.filter((partitionKey) => !skippedOrDiscardedSet.has(partitionKey)));
};

interface Props {
  selectedEvaluation?: EvaluationOrEmpty;
  maxMaterializationsPerMinute: number;
}

export const AutomaterializeMiddlePanelWithPartitions = ({
  selectedEvaluation,
  maxMaterializationsPerMinute,
}: Props) => {
  const conditionToPartitions: Record<ConditionType, string[]> = React.useMemo(() => {
    const conditions = selectedEvaluation?.conditions;
    if (!conditions?.length) {
      return {} as Record<ConditionType, string[]>;
    }
    return Object.fromEntries(
      conditions
        .map((condition) => {
          const {__typename, partitionKeysOrError} = condition;
          if (partitionKeysOrError?.__typename === 'PartitionKeys') {
            return [__typename, partitionKeysOrError.partitionKeys];
          }
          return null;
        })
        .filter((entryOrNull): entryOrNull is [ConditionType, string[]] => !!entryOrNull),
    ) as Record<ConditionType, string[]>;
  }, [selectedEvaluation]);

  const conditionResults = React.useMemo(
    () => new Set(Object.keys(conditionToPartitions)) as Set<ConditionType>,
    [conditionToPartitions],
  );

  const assetKeyDetails = React.useMemo(() => {
    const conditions = selectedEvaluation?.conditions;
    const waitingOn = {} as Record<string, AssetKey[]>;
    const parentUpdated = {} as Record<string, AssetKey[]>;
    const parentWillupdate = {} as Record<string, AssetKey[]>;
    if (conditions?.length) {
      conditions.forEach((condition) => {
        if (condition.__typename === 'ParentOutdatedAutoMaterializeCondition') {
          const {waitingOnAssetKeys, partitionKeysOrError} = condition;
          if (partitionKeysOrError?.__typename === 'PartitionKeys') {
            partitionKeysOrError.partitionKeys.forEach((partitionKey) => {
              const target = [...(waitingOn[partitionKey] || [])];
              target.push(...(waitingOnAssetKeys || []));
              waitingOn[partitionKey] = target;
            });
          }
        } else if (condition.__typename === 'ParentMaterializedAutoMaterializeCondition') {
          const {updatedAssetKeys, willUpdateAssetKeys, partitionKeysOrError} = condition;
          if (partitionKeysOrError?.__typename === 'PartitionKeys') {
            partitionKeysOrError.partitionKeys.forEach((partitionKey) => {
              const target = [...(parentUpdated[partitionKey] || [])];
              target.push(...(updatedAssetKeys || []));
              parentUpdated[partitionKey] = target;
            });
            partitionKeysOrError.partitionKeys.forEach((partitionKey) => {
              const target = [...(parentWillupdate[partitionKey] || [])];
              target.push(...(willUpdateAssetKeys || []));
              parentWillupdate[partitionKey] = target;
            });
          }
        }
      });
    }
    return {waitingOn, parentUpdated, parentWillupdate};
  }, [selectedEvaluation]);

  const headerRight = () => {
    const runIds =
      selectedEvaluation?.__typename === 'AutoMaterializeAssetEvaluationRecord'
        ? selectedEvaluation.runIds
        : [];
    const count = runIds.length;

    if (count === 0 || !selectedEvaluation?.conditions) {
      return null;
    }

    const {conditions} = selectedEvaluation;
    const partitionKeys = extractRequestedPartitionKeys(conditions);
    return (
      <AutomaterializeRequestedPartitionsLink
        runIds={runIds}
        partitionKeys={Array.from(partitionKeys)}
        intent="success"
      />
    );
  };

  return (
    <Box flex={{direction: 'column', grow: 1}}>
      <Box
        style={{flex: '0 0 48px'}}
        padding={{horizontal: 16}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        flex={{alignItems: 'center', justifyContent: 'space-between'}}
      >
        <Subheading>Result</Subheading>
        <div>{headerRight()}</div>
      </Box>
      <ConditionsWithPartitions
        conditionResults={conditionResults}
        conditionToPartitions={conditionToPartitions}
        maxMaterializationsPerMinute={maxMaterializationsPerMinute}
        parentOutdatedWaitingOnAssetKeys={assetKeyDetails.waitingOn}
        parentUpdatedAssetKeys={assetKeyDetails.parentUpdated}
        parentWillUpdateAssetKeys={assetKeyDetails.parentWillupdate}
      />
    </Box>
  );
};
