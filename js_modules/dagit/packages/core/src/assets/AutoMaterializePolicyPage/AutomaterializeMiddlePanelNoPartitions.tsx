import {Box, Colors, Subheading} from '@dagster-io/ui';
import * as React from 'react';

import {AssetKey} from '../types';

import {AutomaterializeRunTag} from './AutomaterializeRunTag';
import {ConditionType, ConditionsNoPartitions} from './Conditions';
import {EvaluationOrEmpty} from './types';

interface Props {
  selectedEvaluation?: EvaluationOrEmpty;
}

export const AutomaterializeMiddlePanelNoPartitions = ({selectedEvaluation}: Props) => {
  const conditionResults = React.useMemo(() => {
    return new Set(
      (selectedEvaluation?.conditions || []).map((condition) => condition.__typename),
    ) as Set<ConditionType>;
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

    return <AutomaterializeRunTag runId={runIds[0]!} />;
  };

  const assetKeyDetails = React.useMemo(() => {
    if (!selectedEvaluation?.conditions) {
      return {
        waitingOnAssetKeys: [],
        parentUpdatedAssetKeys: [],
        parentWillUpdateAssetKeys: [],
      };
    }
    const waitingOnAssetKeys: AssetKey[] = [];
    const parentUpdatedAssetKeys: AssetKey[] = [];
    const parentWillUpdateAssetKeys: AssetKey[] = [];
    selectedEvaluation.conditions.forEach((condition) => {
      if (condition.__typename === 'ParentOutdatedAutoMaterializeCondition') {
        waitingOnAssetKeys.push(...(condition.waitingOnAssetKeys || []));
      } else if (condition.__typename === 'ParentMaterializedAutoMaterializeCondition') {
        parentUpdatedAssetKeys.push(...(condition.updatedAssetKeys || []));
        parentWillUpdateAssetKeys.push(...(condition.willUpdateAssetKeys || []));
      }
    });
    return {
      waitingOnAssetKeys,
      parentUpdatedAssetKeys,
      parentWillUpdateAssetKeys,
    };
  }, [selectedEvaluation]);

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
      <ConditionsNoPartitions
        conditionResults={conditionResults}
        parentOutdatedWaitingOnAssetKeys={assetKeyDetails.waitingOnAssetKeys}
        parentUpdatedAssetKeys={assetKeyDetails.parentUpdatedAssetKeys}
        parentWillUpdateAssetKeys={assetKeyDetails.parentWillUpdateAssetKeys}
      />
    </Box>
  );
};
