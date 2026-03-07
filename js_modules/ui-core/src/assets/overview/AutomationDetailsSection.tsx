import {Body, Box, Popover, Tag} from '@dagster-io/ui-components';
import {useMemo} from 'react';

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
          <Box flex={{direction: 'column', gap: 12}}>
            <Popover
              placement="top"
              interactionKind="hover"
              content={
                <Body>
                  <Box padding={{vertical: 12, horizontal: 16}} style={{maxWidth: '300px'}}>
                    This is a legacy freshness policy, and will not appear in observability
                    features.{' '}
                    <a
                      href="https://docs.dagster.io/guides/observe/asset-freshness-policies"
                      target="_blank"
                      rel="noreferrer"
                    >
                      Learn how to upgrade
                    </a>{' '}
                    to use the new freshness policy API.
                  </Box>
                </Body>
              }
            >
              <Tag intent="warning" icon="freshness">
                Legacy freshness policy
              </Tag>
            </Popover>
            <div>
              <Body>{freshnessPolicyDescription(assetNode.freshnessPolicy)}</Body>
            </div>
          </Box>
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
