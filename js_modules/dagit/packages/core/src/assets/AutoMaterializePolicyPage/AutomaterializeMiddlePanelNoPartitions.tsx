import {Box, Colors, Subheading} from '@dagster-io/ui';
import * as React from 'react';

import {AssetKey} from '../types';

import {AutomaterializeRunTag} from './AutomaterializeRunTag';
import {ConditionType, ConditionsNoPartitions} from './Conditions';
import {EvaluationOrEmpty} from './types';

interface Props {
  selectedEvaluation?: EvaluationOrEmpty;
  maxMaterializationsPerMinute: number;
}

export const AutomaterializeMiddlePanelNoPartitions = ({
  selectedEvaluation,
  maxMaterializationsPerMinute,
}: Props) => {
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
      return <small>Not launched</small>;
    }

    return <AutomaterializeRunTag runId={runIds[0]!} />;
  };

  const parentOutdatedWaitingOnAssetKeys = React.useMemo(() => {
    if (!selectedEvaluation?.conditions) {
      return [];
    }
    const waitingOnAssetKeys: AssetKey[] = [];
    selectedEvaluation.conditions.forEach((condition) => {
      if (condition.__typename === 'ParentOutdatedAutoMaterializeCondition') {
        waitingOnAssetKeys.push(...(condition.waitingOnAssetKeys || []));
      }
    });
    return waitingOnAssetKeys;
  }, [selectedEvaluation]);

  return (
    <Box flex={{direction: 'column', grow: 1}}>
      <Box
        style={{flex: '0 0 48px'}}
        padding={{horizontal: 16}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        flex={{alignItems: 'center', justifyContent: 'space-between'}}
      >
        <Subheading>Evaluation</Subheading>
      </Box>
      <ConditionsNoPartitions
        conditionResults={conditionResults}
        maxMaterializationsPerMinute={maxMaterializationsPerMinute}
        parentOutdatedWaitingOnAssetKeys={parentOutdatedWaitingOnAssetKeys}
      />
      <Box
        // style={{flex: '0 0 96px'}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        flex={{alignItems: 'center', justifyContent: 'space-between'}}
      >
        <Box
          style={{flex: '0', backgroundColor: Colors.Gray100}}
          padding={{horizontal: 32, vertical: 24}}
        >
          <Subheading>Result</Subheading>
        </Box>
        <Box flex={{alignItems: 'flex-end'}} padding={{horizontal: 16}}>
          <div>{headerRight()}</div>
        </Box>
      </Box>
    </Box>
  );
};
