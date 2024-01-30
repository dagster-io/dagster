import {gql} from '@apollo/client';
import {
  Body,
  Body2,
  Box,
  Caption,
  Colors,
  Icon,
  Subtitle1,
  Subtitle2,
  Tag,
  Tooltip,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {ASSET_NODE_FRAGMENT} from '../asset-graph/AssetNode';
import {AssetNodeForGraphQueryFragment} from '../asset-graph/types/useAssetGraphData.types';
import {DagsterTypeSummary} from '../dagstertype/DagsterType';
import {AssetCheckExecutionResolvedStatus, AssetCheckSeverity} from '../graphql/types';
import {Description} from '../pipelines/Description';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {countBy} from 'lodash';
import {Timestamp} from '../app/time/Timestamp';
import {LiveDataForNode} from '../asset-graph/Utils';
import {AssetComputeKindTag} from '../graph/OpTags';
import {RepositoryLink} from '../nav/RepositoryLink';
import {titleForRun} from '../runs/RunUtils';
import {ASSET_NODE_CONFIG_FRAGMENT} from './AssetConfig';
import {AssetDefinedInMultipleReposNotice} from './AssetDefinedInMultipleReposNotice';
import {
  ASSET_NODE_OP_METADATA_FRAGMENT,
  AssetMetadataTable,
  metadataForAssetNode,
} from './AssetMetadata';
import {useAutomationPolicySensorFlag} from './AutomationPolicySensorFlag';
import {OverdueTag} from './OverdueTag';
import {StaleReasonsTags} from './Stale';
import {UnderlyingOpsOrGraph} from './UnderlyingOpsOrGraph';
import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinition.types';
import {useAutomaterializeDaemonStatus} from './useAutomaterializeDaemonStatus';

export const AssetNodeOverview = ({
  assetNode,
  liveData,
  upstream,
  downstream,
}: {
  assetNode: AssetNodeDefinitionFragment;
  liveData: LiveDataForNode;
  upstream: AssetNodeForGraphQueryFragment[] | null;
  downstream: AssetNodeForGraphQueryFragment[] | null;
  dependsOnSelf: boolean;
}) => {
  const {assetMetadata, assetType} = metadataForAssetNode(assetNode);
  const configType = assetNode.configField?.configType;
  const assetConfigSchema = configType && configType.key !== 'Any' ? configType : null;

  const repoAddress = buildRepoAddress(
    assetNode.repository.name,
    assetNode.repository.location.name,
  );
  const latestMaterializationTimestamp = liveData?.lastMaterialization?.timestamp;
  return (
    <>
      <Box flex={{direction: 'column', gap: 12}} padding={{vertical: 12, horizontal: 24}}>
        <AssetDefinedInMultipleReposNotice
          assetKey={assetNode.assetKey}
          loadedFromRepo={repoAddress}
          padded={true}
        />
        <Box flex={{direction: 'row', gap: 12}}>
          <LatestExecutionCard liveData={liveData} />
          <ChecksCard liveData={liveData} definition={assetNode} />
          <DataFreshnessCard liveData={liveData} definition={assetNode} />
          <ReconciliationCard liveData={liveData} definition={assetNode} />
          <AutomationCard definition={assetNode} />
        </Box>
        <DescriptionSection assetNode={assetNode} />
        <DefinitionSection assetNode={assetNode} />
        <MetadataSection assetNode={assetNode} />
        <ColumnSchemaSection assetNode={assetNode} />
        <LineageSection assetNode={assetNode} upstream={upstream} downstream={downstream} />
      </Box>
    </>
  );
};

const BaseCard = ({children, header}: {children: React.ReactNode; header: React.ReactNode}) => (
  <Box
    border="all"
    flex={{direction: 'row', gap: 24, alignItems: 'start'}}
    padding={{vertical: 16, horizontal: 16}}
    style={{width: '100%', background: Colors.backgroundLight(), borderRadius: 12}}
  >
    <Box flex={{direction: 'column', gap: 4}} style={{flex: 1}}>
      <Box
        flex={{direction: 'row', justifyContent: 'space-between'}}
        border={'bottom'}
        padding={{bottom: 4}}
        margin={{bottom: 4}}
        style={{flex: 1}}
      >
        {header}
      </Box>
      {children}
    </Box>
  </Box>
);

const LatestExecutionCard = ({liveData}: {liveData: LiveDataForNode}) => {
  const materializationInProgress = liveData?.inProgressRunIds[0];
  const unstartedRun = liveData?.unstartedRunIds[0];
  const materializationFailed = liveData?.runWhichFailedToMaterialize?.id;
  const latestMaterializationTimestamp = liveData?.lastMaterialization?.timestamp;
  const missing = liveData?.staleStatus === 'MISSING';

  return (
    <BaseCard
      header={
        <>
          <Subtitle2>Latest materialization</Subtitle2>
          <Link to={'?view=executions'}>Details</Link>
        </>
      }
    >
      <div>
        {materializationInProgress && (
          <Tag intent="primary" icon="spinner">
            {titleForRun({id: materializationInProgress})}
          </Tag>
        )}
        {unstartedRun && (
          <Tag intent="primary" icon="spinner">
            {titleForRun({id: unstartedRun})}
          </Tag>
        )}
        {materializationFailed && (
          <Tag intent="danger" icon="warning_outline">
            {titleForRun({id: materializationFailed})}
          </Tag>
        )}
        {missing && !materializationFailed && !materializationInProgress && !unstartedRun && (
          <Tag intent="warning" icon="status">
            Missing
          </Tag>
        )}
        {!materializationFailed && !materializationInProgress && !unstartedRun && !missing && (
          <Box flex={{direction: 'column', gap: 4}}>
            <div>
              <Tag intent="success" icon="check_circle">
                <Timestamp timestamp={{ms: Number(latestMaterializationTimestamp)}} />
              </Tag>
            </div>
            <Caption style={{color: Colors.textLight()}}>
              Launched by <Link to="/sensors">my_sensor_name</Link>
            </Caption>
          </Box>
        )}
      </div>
    </BaseCard>
  );
};

const AutomationCard = ({definition}: {definition: AssetNodeDefinitionFragment}) => {
  const automaterializeSensorsFlagState = useAutomationPolicySensorFlag();
  const {paused} = useAutomaterializeDaemonStatus();

  return (
    <BaseCard
      header={
        <>
          <Subtitle2>Automation</Subtitle2>
          <Link to={'?view=automation'}>Details</Link>
        </>
      }
    >
      {automaterializeSensorsFlagState === 'has-global-amp' && definition?.autoMaterializePolicy ? (
        <Box flex={{direction: 'column', gap: 4}} style={{flex: 1}}>
          <Tooltip
            content={
              paused ? (
                <Box flex={{direction: 'column'}}>
                  <span>Sensor is paused.</span>{' '}
                  <span>New materializations will not be triggered by automation policies.</span>
                </Box>
              ) : (
                'asset_automation_sensor is running, evaluates every 30s'
              )
            }
            canShow={paused}
          >
            <div>
              <Tag icon="automator" animatedIcon={paused} intent={paused ? 'warning' : 'primary'}>
                <Link to="/overview/automaterialize" style={{outline: 'none'}}>
                  {' '}
                  my_sensor_name{' '}
                </Link>
              </Tag>
            </div>
          </Tooltip>
          <Caption style={{color: Colors.textDisabled()}}>
            {paused ? 'Paused. Not evaluating' : 'Evaluating every 30 seconds'}
          </Caption>
        </Box>
      ) : (
        <Caption style={{color: Colors.textDisabled()}}>No automation policy defined</Caption>
      )}
    </BaseCard>
  );
};

const ChecksCard = ({
  liveData,
  definition,
}: {
  liveData: LiveDataForNode;
  definition: AssetNodeDefinitionFragment;
}) => {
  const checkStatusByResultType = countBy(liveData?.assetChecks, (c: any) => {
    const status = c.executionForLatestMaterialization?.status;
    const value: any =
      status === undefined
        ? 'NOT_EVALUATED'
        : status === AssetCheckExecutionResolvedStatus.FAILED
        ? c.executionForLatestMaterialization?.evaluation?.severity === AssetCheckSeverity.WARN
          ? 'WARN'
          : 'ERROR'
        : status === AssetCheckExecutionResolvedStatus.EXECUTION_FAILED
        ? 'ERROR'
        : status;
    return value;
  });
  const checkResults: any = checkStatusByResultType ? checkStatusByResultType : null;

  return (
    <BaseCard
      header={
        <>
          <Subtitle2>Checks</Subtitle2>
          <Link to={'?view=checks'}>Details</Link>
        </>
      }
    >
      <div>
        {!definition?.hasAssetChecks && (
          <Caption style={{color: Colors.textDisabled()}}>No checks defined</Caption>
        )}
        <Box flex={{direction: 'row', gap: 4, wrap: 'wrap'}}>
          {checkResults?.NOT_EVALUATED && (
            <Tag icon="status" intent="none">
              {checkResults.NOT_EVALUATED} not executed
            </Tag>
          )}
          {checkResults?.IN_PROGRESS && (
            <Tag icon="spinner" intent="primary">
              {checkResults.IN_PROGRESS} running...
            </Tag>
          )}
          {checkResults?.SUCCEEDED && (
            <Tag icon="check_circle" intent="success">
              {checkResults.SUCCEEDED} passed
            </Tag>
          )}
          {checkResults?.WARN && (
            <Tag icon="warning_outline" intent="warning">
              {checkResults.WARN} warning
            </Tag>
          )}
          {checkResults?.ERROR && (
            <Tag icon="cancel" intent="danger">
              {checkResults.ERROR} failed
            </Tag>
          )}
        </Box>
      </div>
    </BaseCard>
  );
};

const DataFreshnessCard = ({
  liveData,
  definition,
}: {
  liveData: LiveDataForNode;
  definition: AssetNodeDefinitionFragment;
}) => {
  const latestMaterilization = liveData?.lastMaterialization?.timestamp;
  const latestMaterializationTimestamp = latestMaterilization && parseInt(latestMaterilization, 10);
  const latestMaterializationDate =
    latestMaterializationTimestamp && new Date(latestMaterializationTimestamp);
  const lagMinutes = definition?.freshnessPolicy?.maximumLagMinutes;
  const expirationDate = latestMaterializationDate
    ? new Date(latestMaterializationDate.getTime() + (lagMinutes || 0) * 60000)
    : null;
  const expired =
    liveData?.freshnessInfo?.currentMinutesLate && liveData?.freshnessInfo?.currentMinutesLate > 0;
  const missing = liveData?.staleStatus === 'MISSING';

  return (
    <BaseCard header={<Subtitle2>Data freshness</Subtitle2>}>
      <div>
        {definition && definition.freshnessPolicy && (
          <Box flex={{direction: 'column', gap: 4, alignItems: 'start'}}>
            <OverdueTag
              policy={definition.freshnessPolicy}
              assetKey={definition.assetKey}
              includeFreshLabel
            />
            {!missing && (
              <Caption style={{color: Colors.textDisabled()}}>
                {expired ? 'Expired ' : 'Expires '}
                <Timestamp timestamp={{ms: Number(expirationDate)}} />
              </Caption>
            )}
          </Box>
        )}
        {definition && !definition.freshnessPolicy && (
          <Box flex={{direction: 'column', gap: 4, alignItems: 'start'}}>
            <Caption style={{color: Colors.textDisabled()}}>No freshness policy defined</Caption>
          </Box>
        )}
      </div>
    </BaseCard>
  );
};

const ReconciliationCard = ({
  definition,
  liveData,
}: {
  liveData: LiveDataForNode;
  definition: AssetNodeDefinitionFragment;
}) => {
  const stale = liveData?.staleStatus === 'STALE';
  const missing = liveData?.staleStatus === 'MISSING';
  return (
    <BaseCard header={<Subtitle2>Reconciliation status</Subtitle2>}>
      <Box>
        {definition && missing && (
          <Box flex={{direction: 'column', gap: 4, wrap: 'wrap'}}>
            <Caption style={{color: Colors.textDisabled()}}>
              Asset has never been materialized
            </Caption>
          </Box>
        )}

        {definition && !missing && stale && (
          <Box flex={{direction: 'row', gap: 4, wrap: 'wrap'}}>
            <StaleReasonsTags liveData={liveData} assetKey={definition.assetKey} include="all" />
          </Box>
        )}
        {definition && !stale && !missing && (
          <Box flex={{direction: 'column', gap: 4, alignItems: 'start'}}>
            <Tag intent="success" icon="check_circle">
              Up to date
            </Tag>
            <Caption style={{color: Colors.textDisabled()}}>No changes to reconcile</Caption>
          </Box>
        )}
      </Box>
    </BaseCard>
  );
};

const BaseSection = ({title, children}: {title: string; children: React.ReactNode}) => {
  const [isOpen, setIsOpen] = React.useState(true);

  return (
    <Box flex={{direction: 'column', gap: 0}}>
      <Box
        border="top"
        padding={{top: 12, horizontal: 12}}
        flex={{direction: 'row', gap: 4, alignItems: 'center'}}
        style={{cursor: 'pointer', userSelect: 'none'}}
        onClick={() => setIsOpen(!isOpen)}
      >
        <Icon
          name="arrow_drop_down"
          style={{transform: isOpen ? 'rotate(0deg)' : 'rotate(-90deg)'}}
        />
        <Subtitle1 style={{color: Colors.textLight()}}>{title}</Subtitle1>
      </Box>
      <Box padding={{vertical: 0, horizontal: 16}} style={{display: isOpen ? 'block' : 'none'}}>
        {children}
      </Box>
    </Box>
  );
};
const DescriptionSection = ({assetNode}: {assetNode: AssetNodeDefinitionFragment}) => {
  return (
    <BaseSection title="Description">
      {assetNode.description ? (
        <Description description={assetNode.description} maxHeight={10000} />
      ) : (
        <Body style={{display: 'block', paddingTop: '12px', color: Colors.textDisabled()}}>
          No description provided
        </Body>
      )}
    </BaseSection>
  );
};

const DefinitionSection = ({assetNode}: {assetNode: AssetNodeDefinitionFragment}) => {
  const [isOpen, setIsOpen] = React.useState(true);
  const repoAddress = buildRepoAddress(
    assetNode.repository.name,
    assetNode.repository.location.name,
  );
  const codeVersion = assetNode.opVersion ? (
    assetNode.opVersion
  ) : (
    <Body2 style={{color: Colors.textDisabled()}}>Not set</Body2>
  );
  const freshnessPolicy = assetNode.freshnessPolicy ? (
    `Data may be no more than ${assetNode?.freshnessPolicy.maximumLagMinutes} minutes old at any time`
  ) : (
    <Body2 style={{color: Colors.textDisabled()}}>Not set</Body2>
  );
  const partitionDefinition = assetNode?.partitionDefinition ? (
    assetNode?.partitionDefinition?.description
  ) : (
    <Body2 style={{color: Colors.textDisabled()}}>Not set</Body2>
  );
  const backfillPolicy = assetNode?.backfillPolicy ? (
    assetNode?.backfillPolicy?.description
  ) : (
    <Body2 style={{color: Colors.textDisabled()}}>
      Not set. Defaults to multiple runs, with a maximum of 1 partition per run
    </Body2>
  );
  const buildAutomationPolicyDescription = (policy: any) => {
    return policy.map((rule: any, idx: number) => {
      const tagColor = (type: string) => {
        switch (type) {
          case 'MATERIALIZE':
            return 'primary';
            break;
          case 'DISCARD':
            return 'danger';
            break;
          default:
            return 'none';
        }
      };

      return (
        <Tooltip key={idx} content={`${rule.decisionType} if ${rule.description}`}>
          <Tag key={idx} intent={tagColor(rule.decisionType)}>
            {rule.decisionType} if {rule.description}
          </Tag>
        </Tooltip>
      );
    });
  };

  return (
    <BaseSection title="Definition">
      <table
        style={{
          width: '100%',
          padding: '12px',
          background: Colors.backgroundLight(),
          borderRadius: 12,
          border: `1px solid ${Colors.keylineDefault()}`,
        }}
      >
        <tbody>
          <tr>
            <td
              style={{
                minWidth: '240px',
                paddingBottom: '6px',
                paddingTop: '6px',
                borderBottom: `1px solid ${Colors.keylineDefault()}`,
              }}
            >
              <Subtitle2>Asset key</Subtitle2>
            </td>
            <td
              style={{
                paddingBottom: '6px',
                paddingTop: '6px',
                borderBottom: `1px solid ${Colors.keylineDefault()}`,
              }}
            >
              {assetNode.assetKey.path.join(' : ')}
            </td>
          </tr>
          <tr>
            <td
              style={{
                paddingBottom: '6px',
                paddingTop: '6px',
                borderBottom: `1px solid ${Colors.keylineDefault()}`,
                verticalAlign: 'top',
              }}
            >
              <Subtitle2>Automation policy</Subtitle2>
            </td>
            <td
              style={{
                paddingBottom: '6px',
                paddingTop: '6px',
                borderBottom: `1px solid ${Colors.keylineDefault()}`,
              }}
            >
              <Box flex={{direction: 'row', gap: 4, alignItems: 'center', wrap: 'wrap'}}>
                {assetNode?.autoMaterializePolicy ? (
                  buildAutomationPolicyDescription(assetNode?.autoMaterializePolicy.rules)
                ) : (
                  <Body2 style={{color: Colors.textDisabled()}}>Not set</Body2>
                )}
              </Box>
            </td>
          </tr>
          <tr>
            <td
              style={{
                paddingBottom: '6px',
                paddingTop: '6px',
                borderBottom: `1px solid ${Colors.keylineDefault()}`,
              }}
            >
              <Subtitle2>Backfill policy</Subtitle2>
            </td>
            <td
              style={{
                paddingBottom: '6px',
                paddingTop: '6px',
                borderBottom: `1px solid ${Colors.keylineDefault()}`,
              }}
            >
              {backfillPolicy}
            </td>
          </tr>
          <tr>
            <td
              style={{
                paddingBottom: '6px',
                paddingTop: '6px',
                borderBottom: `1px solid ${Colors.keylineDefault()}`,
              }}
            >
              <Subtitle2>Code location</Subtitle2>
            </td>
            <td
              style={{
                paddingBottom: '6px',
                paddingTop: '6px',
                borderBottom: `1px solid ${Colors.keylineDefault()}`,
              }}
            >
              <Tag icon="folder">
                <RepositoryLink repoAddress={repoAddress} />
              </Tag>
            </td>
          </tr>
          <tr>
            <td
              style={{
                paddingBottom: '6px',
                paddingTop: '6px',
                borderBottom: `1px solid ${Colors.keylineDefault()}`,
              }}
            >
              <Subtitle2>Code version</Subtitle2>
            </td>
            <td
              style={{
                paddingBottom: '6px',
                paddingTop: '6px',
                borderBottom: `1px solid ${Colors.keylineDefault()}`,
              }}
            >
              {codeVersion}
            </td>
          </tr>
          <tr>
            <td
              style={{
                paddingBottom: '6px',
                paddingTop: '6px',
                borderBottom: `1px solid ${Colors.keylineDefault()}`,
              }}
            >
              <Subtitle2>Computed by</Subtitle2>
            </td>
            <td
              style={{
                paddingBottom: '6px',
                paddingTop: '6px',
                borderBottom: `1px solid ${Colors.keylineDefault()}`,
              }}
            >
              {!assetNode.isExecutable && <Tag icon="source_asset">External</Tag>}
              <UnderlyingOpsOrGraph assetNode={assetNode} repoAddress={repoAddress} />
              <AssetComputeKindTag
                style={{position: 'relative'}}
                definition={assetNode}
                reduceColor
              />
            </td>
          </tr>
          <tr>
            <td
              style={{
                paddingBottom: '6px',
                paddingTop: '6px',
                borderBottom: `1px solid ${Colors.keylineDefault()}`,
              }}
            >
              <Subtitle2>Freshness policy</Subtitle2>
            </td>
            <td
              style={{
                paddingBottom: '6px',
                paddingTop: '6px',
                borderBottom: `1px solid ${Colors.keylineDefault()}`,
              }}
            >
              {freshnessPolicy}
            </td>
          </tr>
          <tr>
            <td
              style={{
                paddingBottom: '6px',
                paddingTop: '6px',
                borderBottom: `1px solid ${Colors.keylineDefault()}`,
              }}
            >
              <Subtitle2>Group</Subtitle2>
            </td>
            <td
              style={{
                paddingBottom: '6px',
                paddingTop: '6px',
                borderBottom: `1px solid ${Colors.keylineDefault()}`,
              }}
            >
              <Tag icon="asset_group">
                <Link
                  to={workspacePathFromAddress(repoAddress, `/asset-groups/${assetNode.groupName}`)}
                >
                  {assetNode.groupName}
                </Link>
              </Tag>
            </td>
          </tr>
          <tr>
            <td style={{paddingBottom: '6px', paddingTop: '6px'}}>
              <Subtitle2>Partition definition</Subtitle2>
            </td>
            <td style={{paddingBottom: '6px', paddingTop: '6px'}}>{partitionDefinition}</td>
          </tr>
        </tbody>
      </table>
    </BaseSection>
  );
};

const MetadataSection = ({assetNode}: {assetNode: AssetNodeDefinitionFragment}) => {
  return (
    <BaseSection title="Metadata">
      {assetNode.metadataEntries.length > 0 ? (
        <AssetMetadataTable
          assetMetadata={assetNode.metadataEntries}
          repoLocation={assetNode?.repository?.location.id}
        />
      ) : (
        <Body style={{display: 'block', paddingTop: '12px', color: Colors.textDisabled()}}>
          No metadata provided
        </Body>
      )}
    </BaseSection>
  );
};

const ColumnSchemaSection = ({assetNode}: {assetNode: AssetNodeDefinitionFragment}) => {
  const {assetType} = metadataForAssetNode(assetNode);

  // BG NOTE THIS IS NOT THE COLUMN SCHEMA!

  return (
    <BaseSection title="Column schema">
      {assetType && assetType.displayName !== 'Any' ? (
        <Body style={{display: 'block', paddingTop: '12px', color: Colors.textDisabled()}}>
          <DagsterTypeSummary type={assetType} />
        </Body>
      ) : (
        <Body style={{display: 'block', paddingTop: '12px', color: Colors.textDisabled()}}>
          No schema provided
        </Body>
      )}
    </BaseSection>
  );
};

const LineageSection = ({
  assetNode,
  upstream,
  downstream,
}: {
  assetNode: AssetNodeDefinitionFragment;
  upstream: AssetNodeForGraphQueryFragment[] | null;
  downstream: AssetNodeForGraphQueryFragment[] | null;
}) => {
  return (
    <BaseSection title="Lineage">
      {assetNode.metadataEntries.length > 0 ? (
        <Body style={{display: 'block', paddingTop: '12px', color: Colors.textDisabled()}}>
          Metadata
        </Body>
      ) : (
        <Body style={{display: 'block', paddingTop: '12px', color: Colors.textDisabled()}}>
          No metadata provided
        </Body>
      )}
    </BaseSection>
  );
};

export const ASSET_NODE_DEFINITION_FRAGMENT = gql`
  fragment AssetNodeDefinitionFragment on AssetNode {
    id
    description
    graphName
    opNames
    opVersion
    jobNames
    isSource
    isExecutable
    autoMaterializePolicy {
      policyType
      rules {
        className
        description
        decisionType
      }
    }
    freshnessPolicy {
      maximumLagMinutes
      cronSchedule
      cronScheduleTimezone
    }
    backfillPolicy {
      description
    }
    partitionDefinition {
      description
    }
    repository {
      id
      name
      location {
        id
        name
      }
    }
    requiredResources {
      resourceKey
    }

    ...AssetNodeConfigFragment
    ...AssetNodeFragment
    ...AssetNodeOpMetadataFragment
  }

  ${ASSET_NODE_CONFIG_FRAGMENT}
  ${ASSET_NODE_FRAGMENT}
  ${ASSET_NODE_OP_METADATA_FRAGMENT}
`;
