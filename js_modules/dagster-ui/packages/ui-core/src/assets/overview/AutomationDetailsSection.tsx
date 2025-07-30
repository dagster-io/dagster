import {Body, Box} from '@dagster-io/ui-components';
import React, {useMemo} from 'react';

import {insitigatorsByType} from '../AssetNodeInstigatorTag';
import {AttributeAndValue, SectionEmptyState, SectionSkeleton, isEmptyChildren} from './Common';
import {isHiddenAssetGroupJob} from '../../asset-graph/Utils';
import {ScheduleOrSensorTag} from '../../nav/ScheduleOrSensorTag';
import {PipelineTag} from '../../pipelines/PipelineReference';
import {RepoAddress} from '../../workspace/types';
import {EvaluationUserLabel} from '../AutoMaterializePolicyPage/EvaluationConditionalLabel';
import {freshnessPolicyDescription} from '../OverdueTag';
import {AssetTableDefinitionFragment} from '../types/AssetTableFragment.types';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';

export const AutomationDetailsSection = ({
  repoAddress,
  assetNode,
  cachedOrLiveAssetNode,
}: {
  repoAddress: RepoAddress | null;
  assetNode: AssetViewDefinitionNodeFragment | null | undefined;
  cachedOrLiveAssetNode: AssetViewDefinitionNodeFragment | AssetTableDefinitionFragment;
}) => {
  const {schedules, sensors} = useMemo(() => insitigatorsByType(assetNode), [assetNode]);
  const visibleJobNames =
    cachedOrLiveAssetNode?.jobNames.filter((jobName) => !isHiddenAssetGroupJob(jobName)) || [];

  const attributes = [
    {
      label: 'Jobs',
      children: visibleJobNames.map((jobName) => (
        <PipelineTag
          key={jobName}
          isJob
          showIcon
          pipelineName={jobName}
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          pipelineHrefContext={repoAddress!}
        />
      )),
    },
    {
      label: 'Sensors',
      children: assetNode ? (
        sensors.length > 0 ? (
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          <ScheduleOrSensorTag repoAddress={repoAddress!} sensors={sensors} showSwitch={false} />
        ) : null
      ) : (
        <SectionSkeleton />
      ),
    },
    {
      label: 'Schedules',
      children: assetNode ? (
        schedules.length > 0 && (
          <ScheduleOrSensorTag
            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
            repoAddress={repoAddress!}
            schedules={schedules}
            showSwitch={false}
          />
        )
      ) : (
        <SectionSkeleton />
      ),
    },
    {
      label: 'Freshness policy',
      children: assetNode ? (
        assetNode?.freshnessPolicy && (
          <Body>{freshnessPolicyDescription(assetNode.freshnessPolicy)}</Body>
        )
      ) : (
        <SectionSkeleton />
      ),
    },
    {
      label: 'Automation condition',
      children: assetNode?.automationCondition?.label ? (
        <EvaluationUserLabel
          userLabel={assetNode.automationCondition.label}
          expandedLabel={assetNode.automationCondition.expandedLabel}
        />
      ) : null,
    },
  ];

  if (
    attributes.every((props) => isEmptyChildren(props.children)) &&
    !cachedOrLiveAssetNode.automationCondition
  ) {
    return (
      <SectionEmptyState
        title="No automations found for this asset"
        description="Dagster offers several ways to run data pipelines without manual intervention, including traditional scheduling and event-based triggers."
        learnMoreLink="https://docs.dagster.io/concepts/automation#automation"
      />
    );
  }

  return (
    <Box flex={{direction: 'column', gap: 12}}>
      {attributes.map((props) => (
        <AttributeAndValue key={props.label} {...props} />
      ))}
    </Box>
  );
};
