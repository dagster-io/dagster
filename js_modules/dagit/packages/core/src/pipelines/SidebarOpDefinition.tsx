import {gql} from '@apollo/client';
import {Box, Colors, ConfigTypeSchema, FontFamily, Icon} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {breakOnUnderscores} from '../app/Util';
import {displayNameForAssetKey, isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {OpTypeSignature, OP_TYPE_SIGNATURE_FRAGMENT} from '../ops/OpTypeSignature';
import {pluginForMetadata} from '../plugins';
import {CONFIG_TYPE_SCHEMA_FRAGMENT} from '../typeexplorer/ConfigTypeSchema';
import {DAGSTER_TYPE_WITH_TOOLTIP_FRAGMENT, TypeWithTooltip} from '../typeexplorer/TypeWithTooltip';
import {RepoAddress} from '../workspace/types';

import {Description} from './Description';
import {
  SectionItemContainer,
  SectionSmallHeader,
  SidebarSection,
  SidebarSubhead,
  SidebarTitle,
} from './SidebarComponents';
import {
  Invocation,
  ResourceContainer,
  ResourceHeader,
  ShowAllButton,
  SidebarOpInvocationInfo,
  OpEdges,
  OpMappingTable,
  TypeWrapper,
} from './SidebarOpHelpers';
import {SidebarOpDefinitionFragment} from './types/SidebarOpDefinitionFragment';

interface SidebarOpDefinitionProps {
  definition: SidebarOpDefinitionFragment;
  getInvocations?: (definitionName: string) => {handleID: string}[];
  showingSubgraph: boolean;
  onClickInvocation: (arg: SidebarOpInvocationInfo) => void;
  repoAddress?: RepoAddress;
}

const DEFAULT_INVOCATIONS_SHOWN = 20;

export const SidebarOpDefinition: React.FC<SidebarOpDefinitionProps> = (props) => {
  const {definition, getInvocations, showingSubgraph, onClickInvocation, repoAddress} = props;
  const Plugin = pluginForMetadata(definition.metadata);
  const isComposite = definition.__typename === 'CompositeSolidDefinition';
  const configField = definition.__typename === 'SolidDefinition' ? definition.configField : null;

  const inputMappings: OpMappingTable = {};
  const outputMappings: OpMappingTable = {};

  if (showingSubgraph && definition.__typename === 'CompositeSolidDefinition') {
    definition.inputMappings.forEach(
      (m) =>
        (inputMappings[m.definition.name] = [
          ...(inputMappings[m.definition.name] || []),
          m.mappedInput,
        ]),
    );
    definition.outputMappings.forEach(
      (m) =>
        (outputMappings[m.definition.name] = [
          ...(outputMappings[m.definition.name] || []),
          m.mappedOutput,
        ]),
    );
  }

  let requiredResources = null;
  if (definition.__typename === 'SolidDefinition') {
    requiredResources = definition.requiredResources;
  }

  return (
    <div>
      <SidebarSection title="Definition">
        <Box padding={{vertical: 16, horizontal: 24}}>
          <SidebarSubhead>{isComposite ? 'Graph' : 'Op'}</SidebarSubhead>
          <SidebarTitle>{breakOnUnderscores(definition.name)}</SidebarTitle>
          <OpTypeSignature definition={definition} />
        </Box>
      </SidebarSection>
      {definition.description && (
        <SidebarSection title="Description">
          <Box padding={{vertical: 16, horizontal: 24}}>
            <Description description={definition.description} />
          </Box>
        </SidebarSection>
      )}
      {definition.metadata && Plugin && Plugin.SidebarComponent && (
        <SidebarSection title="Metadata">
          <Box padding={{vertical: 16, horizontal: 24}}>
            <Plugin.SidebarComponent definition={definition} repoAddress={repoAddress} />
          </Box>
        </SidebarSection>
      )}
      {configField && (
        <SidebarSection title="Config">
          <Box padding={{vertical: 16, horizontal: 24}}>
            <ConfigTypeSchema
              type={configField.configType}
              typesInScope={configField.configType.recursiveConfigTypes}
            />
          </Box>
        </SidebarSection>
      )}
      {requiredResources && (
        <SidebarSection title="Required Resources">
          <Box padding={{vertical: 16, horizontal: 24}}>
            {[...requiredResources].sort().map((requirement) => (
              <ResourceContainer key={requirement.resourceKey}>
                <Icon name="resource" color={Colors.Gray700} />
                <ResourceHeader>{requirement.resourceKey}</ResourceHeader>
              </ResourceContainer>
            ))}
          </Box>
        </SidebarSection>
      )}
      <SidebarSection title="Inputs">
        <Box padding={{vertical: 16, horizontal: 24}}>
          {definition.inputDefinitions.map((inputDef, idx) => (
            <SectionItemContainer key={idx}>
              <SectionSmallHeader>{breakOnUnderscores(inputDef.name)}</SectionSmallHeader>
              <TypeWrapper>
                <TypeWithTooltip type={inputDef.type} />
              </TypeWrapper>
              <Description description={inputDef.description} />
              <OpEdges title="Mapped to:" items={inputMappings[inputDef.name]} />
            </SectionItemContainer>
          ))}
        </Box>
      </SidebarSection>
      <SidebarSection title="Outputs">
        <Box padding={{vertical: 16, horizontal: 24}}>
          {definition.outputDefinitions.map((outputDef, idx) => (
            <SectionItemContainer key={idx}>
              <SectionSmallHeader>
                {breakOnUnderscores(outputDef.name)}
                {outputDef.isDynamic && <span title="DynamicOutput">[*]</span>}
              </SectionSmallHeader>
              <TypeWrapper>
                <TypeWithTooltip type={outputDef.type} />
              </TypeWrapper>
              <OpEdges title="Mapped from:" items={outputMappings[outputDef.name]} />
              <Description description={outputDef.description} />
            </SectionItemContainer>
          ))}
        </Box>
      </SidebarSection>
      {definition.assetNodes.length > 0 && (
        <SidebarSection title="Yielded Assets">
          {definition.assetNodes.map((node) => (
            <AssetNodeListItem key={node.id} to={assetDetailsPathForKey(node.assetKey)}>
              <Icon name="asset" /> {displayNameForAssetKey(node.assetKey)}
            </AssetNodeListItem>
          ))}
        </SidebarSection>
      )}
      {getInvocations && (
        <SidebarSection title="All Invocations">
          <InvocationList
            invocations={getInvocations(definition.name)}
            onClickInvocation={onClickInvocation}
          />
        </SidebarSection>
      )}
    </div>
  );
};

export const SIDEBAR_OP_DEFINITION_FRAGMENT = gql`
  fragment SidebarOpDefinitionFragment on ISolidDefinition {
    ...OpTypeSignatureFragment
    __typename
    name
    description
    metadata {
      key
      value
    }
    assetNodes {
      id
      assetKey {
        path
      }
    }
    outputDefinitions {
      name
      description
      isDynamic
      type {
        ...DagsterTypeWithTooltipFragment
      }
    }
    inputDefinitions {
      name
      description
      type {
        ...DagsterTypeWithTooltipFragment
      }
    }
    ... on SolidDefinition {
      requiredResources {
        resourceKey
      }
      configField {
        configType {
          ...ConfigTypeSchemaFragment
          recursiveConfigTypes {
            ...ConfigTypeSchemaFragment
          }
        }
      }
    }
    ... on CompositeSolidDefinition {
      id
      inputMappings {
        definition {
          name
        }
        mappedInput {
          definition {
            name
          }
          solid {
            name
          }
        }
      }
      outputMappings {
        definition {
          name
        }
        mappedOutput {
          definition {
            name
          }
          solid {
            name
          }
        }
      }
    }
  }

  ${DAGSTER_TYPE_WITH_TOOLTIP_FRAGMENT}
  ${OP_TYPE_SIGNATURE_FRAGMENT}
  ${CONFIG_TYPE_SCHEMA_FRAGMENT}
`;

const InvocationList: React.FC<{
  invocations: SidebarOpInvocationInfo[];
  onClickInvocation: (arg: SidebarOpInvocationInfo) => void;
}> = ({invocations, onClickInvocation}) => {
  const [showAll, setShowAll] = React.useState<boolean>(false);
  const visible = invocations.filter((i) => !isHiddenAssetGroupJob(i.pipelineName || ''));
  const clipped = showAll ? visible : visible.slice(0, DEFAULT_INVOCATIONS_SHOWN);

  return (
    <>
      {clipped.map((invocation, idx) => (
        <Invocation
          key={idx}
          invocation={invocation}
          onClick={() => onClickInvocation(invocation)}
        />
      ))}
      {clipped.length < visible.length && (
        <ShowAllButton onClick={() => setShowAll(true)}>
          {`Show ${invocations.length - clipped.length} More Invocations`}
        </ShowAllButton>
      )}
    </>
  );
};

const AssetNodeListItem = styled(Link)`
  user-select: none;
  padding: 12px 24px;
  cursor: pointer;
  border-bottom: 1px solid ${Colors.KeylineGray};
  display: flex;
  gap: 6px;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: ${Colors.Gray50};
  }

  font-family: ${FontFamily.monospace};
`;
