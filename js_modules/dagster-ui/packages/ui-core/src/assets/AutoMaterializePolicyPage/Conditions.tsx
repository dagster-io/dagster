import {Box, Colors, Icon, Tag} from '@dagster-io/ui-components';
import groupBy from 'lodash/groupBy';
import * as React from 'react';

import {assertUnreachable} from '../../app/Util';
import {
  AutoMaterializeDecisionType,
  AutoMaterializeRule,
  AutoMaterializeRuleEvaluation,
} from '../../graphql/types';

import {AutomaterializeRequestedPartitionsLink} from './AutomaterializeRequestedPartitionsLink';
import {CollapsibleSection} from './CollapsibleSection';
import {ParentUpdatedLink} from './ParentUpdatedLink';
import {ParentUpdatedPartitionLink} from './ParentUpdatedPartitionLink';
import {WaitingOnAssetKeysLink} from './WaitingOnAssetKeysLink';
import {WaitingOnPartitionAssetKeysLink} from './WaitingOnPartitionAssetKeysLink';
import {RuleWithEvaluationsFragment} from './types/GetEvaluationsQuery.types';

interface RuleEvaluationOutcomeProps {
  text: string;
  met: boolean;
  rightElement?: React.ReactNode;
}

const RuleEvaluationOutcome = ({text, met, rightElement}: RuleEvaluationOutcomeProps) => {
  return (
    <Box
      flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
      style={{height: 24}}
    >
      <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
        <Icon name={met ? 'done' : 'close'} color={met ? Colors.Dark : Colors.Gray500} />
        <div style={{color: met ? Colors.Dark : Colors.Gray500}}>
          {text.slice(0, 1).toUpperCase()}
          {text.slice(1)}
        </div>
      </Box>
      {rightElement}
    </Box>
  );
};

const SECTIONS: {
  decisionType: AutoMaterializeDecisionType;
  header: string;
  details: string;
  intent?: React.ComponentProps<typeof Tag>['intent'];
  showAlways: boolean;
}[] = [
  {
    decisionType: AutoMaterializeDecisionType.MATERIALIZE,
    header: 'Materialization conditions met',
    details:
      'These conditions trigger a materialization, unless they are blocked by a skip or discard condition.',
    showAlways: true,
  },
  {
    decisionType: AutoMaterializeDecisionType.SKIP,
    header: 'Skip conditions met',
    details: 'Skips will materialize in a future evaluation, once the skip condition is resolved.',
    showAlways: true,
  },
  {
    decisionType: AutoMaterializeDecisionType.DISCARD,
    header: 'Discard conditions met',
    details:
      'Discarded partitions will not be materialized unless new materialization conditions occur. You may want to run a manual backfill to respond to the materialize conditions.',
    intent: 'danger',
    showAlways: false,
  },
];

interface RuleEvaluationOutcomesProps {
  rules: AutoMaterializeRule[];
  ruleEvaluations: RuleWithEvaluationsFragment[];
  assetHasDefinedPartitions: boolean;
}

export const RuleEvaluationOutcomes = ({
  rules,
  ruleEvaluations,
  assetHasDefinedPartitions,
}: RuleEvaluationOutcomesProps) => {
  const groupedRules = groupBy(rules, (rule) => rule.decisionType);
  const evaluationsOfRule = (description: string) => {
    return ruleEvaluations.find((e) => e.rule?.description === description)?.ruleEvaluations || [];
  };

  return (
    <>
      {SECTIONS.filter((section) => section.showAlways || groupedRules[section.decisionType]).map(
        (section) => (
          <CollapsibleSection
            key={section.decisionType}
            header={section.header}
            details={section.details}
          >
            <Box flex={{direction: 'column', gap: 8}}>
              {(groupedRules[section.decisionType] || []).map(({description}) => {
                const evaluations = evaluationsOfRule(description);
                return (
                  <RuleEvaluationOutcome
                    key={description}
                    text={description}
                    met={evaluations.length > 0}
                    rightElement={
                      assetHasDefinedPartitions ? (
                        <RightElementForPartitionedEvaluations
                          evaluations={evaluations}
                          intent={section.intent}
                        />
                      ) : (
                        <RightElementForEvaluations
                          evaluations={evaluations}
                          intent={section.intent}
                        />
                      )
                    }
                  />
                );
              })}
            </Box>
          </CollapsibleSection>
        ),
      )}
    </>
  );
};

const RightElementForEvaluations = ({
  evaluations,
}: {
  evaluations: AutoMaterializeRuleEvaluation[];
  intent?: React.ComponentProps<typeof Tag>['intent'];
}) => {
  console.log(evaluations);
  const first = evaluations.map((e) => e.evaluationData!).find(Boolean);
  if (!first) {
    return <div style={{color: Colors.Gray400}}>&ndash;</div>;
  }
  switch (first.__typename) {
    case 'ParentMaterializedRuleEvaluationData':
      return (
        <ParentUpdatedLink
          updatedAssetKeys={first.updatedAssetKeys || []}
          willUpdateAssetKeys={first.willUpdateAssetKeys || []}
        />
      );
    case 'WaitingOnKeysRuleEvaluationData':
      return <WaitingOnAssetKeysLink assetKeys={first.waitingOnAssetKeys || []} />;
    case 'TextRuleEvaluationData':
      return first.text;
    default:
      assertUnreachable(first);
  }
};

const partitionKeysOf = (e: AutoMaterializeRuleEvaluation) =>
  e.partitionKeysOrError?.__typename === 'PartitionKeys'
    ? e.partitionKeysOrError.partitionKeys
    : [];

const RightElementForPartitionedEvaluations = ({
  evaluations,
  intent,
}: {
  evaluations: AutoMaterializeRuleEvaluation[];
  intent?: React.ComponentProps<typeof Tag>['intent'];
}) => {
  const evaluationsWithData = evaluations.filter((e) => !!e.evaluationData);
  const first = evaluations[0];
  if (!first) {
    return (
      <AutomaterializeRequestedPartitionsLink
        partitionKeys={evaluations.flatMap(partitionKeysOf)}
        intent={intent}
      />
    );
  }

  const typename = first.evaluationData!.__typename;

  switch (typename) {
    case 'ParentMaterializedRuleEvaluationData':
      const updatedAssetKeys = Object.fromEntries(
        evaluationsWithData.flatMap((e) =>
          partitionKeysOf(e).map((key) => [
            key,
            (e.evaluationData?.__typename === 'ParentMaterializedRuleEvaluationData' &&
              e.evaluationData.updatedAssetKeys) ||
              [],
          ]),
        ),
      );
      const willUpdateAssetKeys = Object.fromEntries(
        evaluationsWithData.flatMap((e) =>
          partitionKeysOf(e).map((key) => [
            key,
            (e.evaluationData?.__typename === 'ParentMaterializedRuleEvaluationData' &&
              e.evaluationData.willUpdateAssetKeys) ||
              [],
          ]),
        ),
      );

      return (
        <ParentUpdatedPartitionLink
          updatedAssetKeys={updatedAssetKeys}
          willUpdateAssetKeys={willUpdateAssetKeys}
        />
      );
    case 'WaitingOnKeysRuleEvaluationData':
      const assetKeysByPartition = Object.fromEntries(
        evaluationsWithData.flatMap((e) =>
          partitionKeysOf(e).map((key) => [
            key,
            (e.evaluationData?.__typename === 'WaitingOnKeysRuleEvaluationData' &&
              e.evaluationData.waitingOnAssetKeys) ||
              [],
          ]),
        ),
      );
      return <WaitingOnPartitionAssetKeysLink assetKeysByPartition={assetKeysByPartition} />;
    case 'TextRuleEvaluationData':
      return first.evaluationData?.text;
    default:
      assertUnreachable(typename);
  }
};
