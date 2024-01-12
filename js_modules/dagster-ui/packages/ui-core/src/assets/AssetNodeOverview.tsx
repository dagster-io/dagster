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
import {AutomaterializeDaemonStatusTag} from './AutomaterializeDaemonStatusTag';
import {useAutomationPolicySensorFlag} from './AutomationPolicySensorFlag';
import {OverdueTag} from './OverdueTag';
import {StaleReasonsTags} from './Stale';
import {UnderlyingOpsOrGraph} from './UnderlyingOpsOrGraph';
import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinition.types';

export const AssetNodeOverview = ({
  assetNode,
  liveData,
  upstream,
  downstream,
  dependsOnSelf,
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
  console.log('LIVE DATA');
  console.log(liveData);
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
        <DescriptionCard assetNode={assetNode} />
        <DefinitionCard assetNode={assetNode} />
        <MetaDataCard assetNode={assetNode} />
        <ColumnsCard assetNode={assetNode} />
        <LineageCard assetNode={assetNode} upstream={upstream} downstream={downstream} />
      </Box>
    </>
  );
};

const LatestExecutionCard = ({liveData}: {liveData: LiveDataForNode}) => {
  const materializationInProgress = liveData?.inProgressRunIds[0];
  const unstartedRun = liveData?.unstartedRunIds[0];
  const materializationFailed = liveData?.runWhichFailedToMaterialize?.id;
  const latestMaterializationTimestamp = liveData?.lastMaterialization?.timestamp;
  const missing = liveData?.staleStatus === 'MISSING';
  console.log(liveData);
  return (
    <Box
      flex={{direction: 'row', gap: 24, alignItems: 'start'}}
      padding={{vertical: 16, horizontal: 16}}
      style={{
        width: '100%',
        background: Colors.backgroundLight(),
        borderRadius: 12,
        border: `1px solid ${Colors.keylineDefault()}`,
      }}
    >
      <Box flex={{direction: 'column', gap: 4}} style={{flex: 1}}>
        <Box
          flex={{direction: 'row', justifyContent: 'space-between'}}
          style={{
            flex: 1,
            paddingBottom: '4px',
            marginBottom: '4px',
            borderBottom: `1px solid ${Colors.keylineDefault()}`,
          }}
        >
          <Subtitle2>Latest materialization</Subtitle2>
          <Link to={'?view=executions'}>Details</Link>
        </Box>
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
      </Box>
    </Box>
  );
};

const AutomationCard = ({definition}: {definition: AssetNodeDefinitionFragment}) => {
  const automaterializeSensorsFlagState = useAutomationPolicySensorFlag();
  return (
    <Box
      flex={{direction: 'row', gap: 24, alignItems: 'start'}}
      padding={{vertical: 16, horizontal: 16}}
      style={{
        width: '100%',
        background: Colors.backgroundLight(),
        borderRadius: 12,
        border: `1px solid ${Colors.keylineDefault()}`,
      }}
    >
      <Box flex={{direction: 'column', gap: 4}} style={{flex: 1}}>
        <Box
          flex={{direction: 'row', justifyContent: 'space-between'}}
          style={{
            flex: 1,
            paddingBottom: '4px',
            marginBottom: '4px',
            borderBottom: `1px solid ${Colors.keylineDefault()}`,
          }}
        >
          <Subtitle2>Automation</Subtitle2>
          <Link to={'?view=automation'}>Details</Link>
        </Box>
        <Box>
          {automaterializeSensorsFlagState === 'has-global-amp' &&
          definition?.autoMaterializePolicy ? (
            <AutomaterializeDaemonStatusTag />
          ) : (
            <Caption style={{color: Colors.textDisabled()}}>No automation policy defined</Caption>
          )}
        </Box>
      </Box>
    </Box>
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
  console.log(checkResults);
  return (
    <Box
      flex={{direction: 'row', gap: 24, alignItems: 'start'}}
      padding={{vertical: 16, horizontal: 16}}
      style={{
        width: '100%',
        background: Colors.backgroundLight(),
        borderRadius: 12,
        border: `1px solid ${Colors.keylineDefault()}`,
      }}
    >
      <Box flex={{direction: 'column', gap: 4}} style={{flex: 1}}>
        <Box
          flex={{direction: 'row', justifyContent: 'space-between'}}
          style={{
            flex: 1,
            paddingBottom: '4px',
            marginBottom: '4px',
            borderBottom: `1px solid ${Colors.keylineDefault()}`,
          }}
        >
          <Subtitle2>Checks</Subtitle2>
          <Link to={'?view=checks'}>Details</Link>
        </Box>
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
      </Box>
    </Box>
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
    <Box
      flex={{direction: 'row', gap: 24, alignItems: 'start'}}
      padding={{vertical: 16, horizontal: 16}}
      style={{
        width: '100%',
        background: Colors.backgroundLight(),
        borderRadius: 12,
        border: `1px solid ${Colors.keylineDefault()}`,
      }}
    >
      <Box flex={{direction: 'column', gap: 4}} style={{flex: 1}}>
        <Box
          flex={{direction: 'row', justifyContent: 'space-between'}}
          style={{
            flex: 1,
            paddingBottom: '4px',
            marginBottom: '4px',
            borderBottom: `1px solid ${Colors.keylineDefault()}`,
          }}
        >
          <Subtitle2>Data freshness</Subtitle2>
        </Box>
        <div>
          {definition && definition.freshnessPolicy && (
            <Box flex={{direction: 'column', gap: 4, alignItems: 'start'}}>
              <OverdueTag policy={definition.freshnessPolicy} assetKey={definition.assetKey} />
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
      </Box>
    </Box>
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
    <Box
      flex={{direction: 'row', gap: 24, alignItems: 'start'}}
      padding={{vertical: 16, horizontal: 16}}
      style={{
        width: '100%',
        background: Colors.backgroundLight(),
        borderRadius: 12,
        border: `1px solid ${Colors.keylineDefault()}`,
      }}
    >
      <Box flex={{direction: 'column', gap: 4}} style={{flex: 1}}>
        <Box
          flex={{direction: 'row', justifyContent: 'space-between'}}
          style={{
            flex: 1,
            paddingBottom: '4px',
            marginBottom: '4px',
            borderBottom: `1px solid ${Colors.keylineDefault()}`,
          }}
        >
          <Subtitle2>Reconciliation status</Subtitle2>
        </Box>
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
      </Box>
    </Box>
  );
};

const StatusCard = ({
  assetNode,
  liveData,
}: {
  assetNode: AssetNodeDefinitionFragment;
  liveData: LiveDataForNode;
}) => (
  <Box
    flex={{direction: 'row', gap: 24}}
    padding={{vertical: 16, horizontal: 16}}
    style={{
      background: Colors.backgroundLight(),
      borderRadius: 12,
      border: `1px solid ${Colors.keylineDefault()}`,
    }}
  >
    <Box flex={{direction: 'column', gap: 4}} style={{flex: 1}}>
      <Box flex={{direction: 'row', justifyContent: 'space-between'}} style={{flex: 1}}>
        <Subtitle2>Latest execution</Subtitle2>
        <Link to={'?view=executions'}>Details</Link>
      </Box>
      <div>
        <Tag intent="success" icon="check_circle">
          <Link to="?view=executions">{liveData?.lastMaterialization?.timestamp}</Link>
        </Tag>
      </div>
    </Box>

    <Box
      flex={{direction: 'column', gap: 4}}
      padding={{left: 24}}
      style={{flex: 1, borderLeft: `1px solid ${Colors.keylineDefault()}`}}
    >
      <Box flex={{direction: 'row', justifyContent: 'space-between'}} style={{flex: 1}}>
        <Subtitle2>Checks</Subtitle2>
        <Link to={'?view=checks'}>Details</Link>
      </Box>
      <Box flex={{direction: 'row', gap: 4}}>
        {assetNode?.hasAssetChecks ? (
          'Checks'
        ) : (
          <Caption style={{color: Colors.textLight()}}>No checks defined</Caption>
        )}
      </Box>
    </Box>

    <Box
      flex={{direction: 'column', gap: 4}}
      padding={{left: 24}}
      style={{flex: 1, borderLeft: `1px solid ${Colors.keylineDefault()}`}}
    >
      <Subtitle2>Freshness</Subtitle2>
      <Box flex={{direction: 'row', gap: 4}}>
        <Tag intent="success" icon="check_circle">
          Data
        </Tag>
        <Tag intent="success" icon="check_circle">
          Code
        </Tag>
        <Tag intent="success" icon="check_circle">
          Deps
        </Tag>
      </Box>
    </Box>

    <Box
      flex={{direction: 'column', gap: 4}}
      padding={{left: 24}}
      style={{flex: 1, borderLeft: `1px solid ${Colors.keylineDefault()}`}}
    >
      <Subtitle2>Upstream changes</Subtitle2>
      <Box flex={{direction: 'row', gap: 4}}>
        <Tag intent="warning" icon="warning_outline">
          Data
        </Tag>
        <Tag intent="success" icon="check_circle">
          Code
        </Tag>
        <Tag intent="success" icon="check_circle">
          Deps
        </Tag>
      </Box>
    </Box>
  </Box>
);

const DescriptionCard = ({assetNode}: {assetNode: AssetNodeDefinitionFragment}) => {
  const [isOpen, setIsOpen] = React.useState(true);

  return (
    <Box flex={{direction: 'column', gap: 0}}>
      <Box
        padding={{top: 12, horizontal: 12}}
        border="top"
        flex={{direction: 'row', gap: 4, alignItems: 'center'}}
        onClick={() => setIsOpen(!isOpen)}
        style={{cursor: 'pointer', userSelect: 'none'}}
      >
        <Icon
          name="arrow_drop_down"
          style={{transform: isOpen ? 'rotate(0deg)' : 'rotate(-90deg)'}}
        />
        <Subtitle1 style={{color: Colors.textLight()}}>Description</Subtitle1>
      </Box>
      <Box padding={{vertical: 0, horizontal: 16}} style={{display: isOpen ? 'block' : 'none'}}>
        {assetNode.description ? (
          <Description description={assetNode.description} maxHeight={10000} />
        ) : (
          <Body style={{display: 'block', paddingTop: '12px', color: Colors.textDisabled()}}>
            No description provided
          </Body>
        )}
      </Box>
    </Box>
  );
};

const DefinitionCard = ({assetNode}: {assetNode: AssetNodeDefinitionFragment}) => {
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
  const autoMaterializePolicy2 = assetNode?.autoMaterializePolicy ? (
    buildAutomationPolicyDescription(assetNode?.autoMaterializePolicy.rules)
  ) : (
    <Body2 style={{color: Colors.textDisabled()}}>Not set</Body2>
  );

  console.log(assetNode);
  return (
    <Box flex={{direction: 'column', gap: 0}}>
      <Box
        padding={{top: 12, horizontal: 12}}
        border="top"
        flex={{direction: 'row', gap: 4, alignItems: 'center'}}
        onClick={() => setIsOpen(!isOpen)}
        style={{cursor: 'pointer', userSelect: 'none'}}
      >
        <Icon
          name="arrow_drop_down"
          style={{transform: isOpen ? 'rotate(0deg)' : 'rotate(-90deg)'}}
        />
        <Subtitle1 style={{color: Colors.textLight()}}>Definition</Subtitle1>
      </Box>
      <Box padding={{vertical: 12, horizontal: 0}} style={{display: isOpen ? 'block' : 'none'}}>
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
                  {autoMaterializePolicy2}
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
                    to={workspacePathFromAddress(
                      repoAddress,
                      `/asset-groups/${assetNode.groupName}`,
                    )}
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
      </Box>
    </Box>
  );
};

const MetaDataCard = ({assetNode}: {assetNode: AssetNodeDefinitionFragment}) => {
  const [isOpen, setIsOpen] = React.useState(true);

  return (
    <Box flex={{direction: 'column', gap: 0}}>
      <Box
        padding={{top: 12, horizontal: 12}}
        border="top"
        flex={{direction: 'row', gap: 4, alignItems: 'center'}}
        onClick={() => setIsOpen(!isOpen)}
        style={{cursor: 'pointer', userSelect: 'none'}}
      >
        <Icon
          name="arrow_drop_down"
          style={{transform: isOpen ? 'rotate(0deg)' : 'rotate(-90deg)'}}
        />
        <Subtitle1 style={{color: Colors.textLight()}}>Metadata</Subtitle1>
      </Box>
      <Box padding={{vertical: 0, horizontal: 16}} style={{display: isOpen ? 'block' : 'none'}}>
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
      </Box>
    </Box>
  );
};

const ColumnsCard = ({assetNode}: {assetNode: AssetNodeDefinitionFragment}) => {
  const [isOpen, setIsOpen] = React.useState(true);
  const metadataEntries = assetNode?.type?.metadataEntries ? assetNode.type.metadataEntries : [];
  return (
    <Box flex={{direction: 'column', gap: 0}}>
      <Box
        padding={{top: 12, horizontal: 12}}
        border="top"
        flex={{direction: 'row', gap: 4, alignItems: 'center'}}
        onClick={() => setIsOpen(!isOpen)}
        style={{cursor: 'pointer', userSelect: 'none'}}
      >
        <Icon
          name="arrow_drop_down"
          style={{transform: isOpen ? 'rotate(0deg)' : 'rotate(-90deg)'}}
        />
        <Subtitle1 style={{color: Colors.textLight()}}>Column schema</Subtitle1>
      </Box>
      <Box padding={{vertical: 0, horizontal: 16}} style={{display: isOpen ? 'block' : 'none'}}>
        {metadataEntries.length > 0 ? (
          <Body style={{display: 'block', paddingTop: '12px', color: Colors.textDisabled()}}>
            <DagsterTypeSummary type={assetNode.type?.metadataEntries} />
          </Body>
        ) : (
          <Body style={{display: 'block', paddingTop: '12px', color: Colors.textDisabled()}}>
            No schema provided
          </Body>
        )}
      </Box>
    </Box>
  );
};

const LineageCard = ({
  assetNode,
  upstream,
  downstream,
}: {
  assetNode: AssetNodeDefinitionFragment;
  upstream: AssetNodeForGraphQueryFragment[] | null;
  downstream: AssetNodeForGraphQueryFragment[] | null;
}) => {
  const [isOpen, setIsOpen] = React.useState(true);
  console.log(upstream);
  console.log(downstream);
  return (
    <Box flex={{direction: 'column', gap: 0}}>
      <Box
        padding={{top: 12, horizontal: 12}}
        border="top"
        flex={{direction: 'row', gap: 4, alignItems: 'center'}}
        onClick={() => setIsOpen(!isOpen)}
        style={{cursor: 'pointer', userSelect: 'none'}}
      >
        <Icon
          name="arrow_drop_down"
          style={{transform: isOpen ? 'rotate(0deg)' : 'rotate(-90deg)'}}
        />
        <Subtitle1 style={{color: Colors.textLight()}}>Lineage</Subtitle1>
      </Box>
      <Box padding={{vertical: 0, horizontal: 16}} style={{display: isOpen ? 'block' : 'none'}}>
        {assetNode.metadataEntries.length > 0 ? (
          <Body style={{display: 'block', paddingTop: '12px', color: Colors.textDisabled()}}>
            Metadata
          </Body>
        ) : (
          <Body style={{display: 'block', paddingTop: '12px', color: Colors.textDisabled()}}>
            No metadata provided
          </Body>
        )}
      </Box>
    </Box>
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
