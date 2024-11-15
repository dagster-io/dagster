import {Box, ButtonLink, Colors, ConfigTypeSchema, Icon, Tag} from '@dagster-io/ui-components';
import React from 'react';
import {Link} from 'react-router-dom';

import {metadataForAssetNode} from '../AssetMetadata';
import {AttributeAndValue, SectionSkeleton} from './Common';
import {showCustomAlert} from '../../app/CustomAlertProvider';
import {COMMON_COLLATOR} from '../../app/Util';
import {DagsterTypeSummary} from '../../dagstertype/DagsterType';
import {RepoAddress} from '../../workspace/types';
import {workspacePathFromAddress} from '../../workspace/workspacePath';
import {UnderlyingOpsOrGraph} from '../UnderlyingOpsOrGraph';
import {AssetNodeDefinitionFragment} from '../types/AssetNodeDefinition.types';

export const ComputeDetailsSection = ({
  repoAddress,
  assetNode,
}: {
  repoAddress: RepoAddress | null;
  assetNode: AssetNodeDefinitionFragment | null | undefined;
}) => {
  if (!assetNode) {
    return <SectionSkeleton />;
  }
  const {assetType} = metadataForAssetNode(assetNode);
  const configType = assetNode?.configField?.configType;
  const assetConfigSchema = configType && configType.key !== 'Any' ? configType : null;

  return (
    <Box flex={{direction: 'column', gap: 12}}>
      <AttributeAndValue label="Computed by">
        <Tag>
          <UnderlyingOpsOrGraph
            assetNode={assetNode}
            repoAddress={repoAddress!}
            hideIfRedundant={false}
          />
        </Tag>
      </AttributeAndValue>

      <AttributeAndValue label="Code version">{assetNode.opVersion}</AttributeAndValue>

      <AttributeAndValue label="Resources">
        {[...assetNode.requiredResources]
          .sort((a, b) => COMMON_COLLATOR.compare(a.resourceKey, b.resourceKey))
          .map((resource) => (
            <Tag key={resource.resourceKey}>
              <Box flex={{gap: 4, alignItems: 'center'}}>
                <Icon name="resource" color={Colors.accentGray()} />
                {repoAddress ? (
                  <Link
                    to={workspacePathFromAddress(repoAddress, `/resources/${resource.resourceKey}`)}
                  >
                    {resource.resourceKey}
                  </Link>
                ) : (
                  resource.resourceKey
                )}
              </Box>
            </Tag>
          ))}
      </AttributeAndValue>

      <AttributeAndValue label="Config schema">
        {assetConfigSchema && (
          <ButtonLink
            onClick={() => {
              showCustomAlert({
                title: 'Config schema',
                body: (
                  <ConfigTypeSchema
                    type={assetConfigSchema}
                    typesInScope={assetConfigSchema.recursiveConfigTypes}
                  />
                ),
              });
            }}
          >
            View config details
          </ButtonLink>
        )}
      </AttributeAndValue>

      <AttributeAndValue label="Type">
        {assetType && assetType.displayName !== 'Any' && (
          <ButtonLink
            onClick={() => {
              showCustomAlert({
                title: 'Type summary',
                body: <DagsterTypeSummary type={assetType} />,
              });
            }}
          >
            View type details
          </ButtonLink>
        )}
      </AttributeAndValue>

      <AttributeAndValue label="Backfill policy">
        {assetNode.backfillPolicy?.description}
      </AttributeAndValue>
    </Box>
  );
};
