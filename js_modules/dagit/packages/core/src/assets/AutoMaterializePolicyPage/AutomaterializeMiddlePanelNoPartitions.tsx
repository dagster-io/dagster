import {Box, Colors, Subheading} from '@dagster-io/ui';
import * as React from 'react';

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
      return null;
    }

    return <AutomaterializeRunTag runId={runIds[0]!} />;
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
      <ConditionsNoPartitions
        conditionResults={conditionResults}
        maxMaterializationsPerMinute={maxMaterializationsPerMinute}
      />
    </Box>
  );
};
