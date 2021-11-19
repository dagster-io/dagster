import {gql} from '@apollo/client';
import * as React from 'react';

import {breakOnUnderscores} from '../app/Util';
import {OpTypeSignature, OP_TYPE_SIGNATURE_FRAGMENT} from '../ops/OpTypeSignature';
import {pluginForMetadata} from '../plugins';
import {ConfigTypeSchema, CONFIG_TYPE_SCHEMA_FRAGMENT} from '../typeexplorer/ConfigTypeSchema';
import {DAGSTER_TYPE_WITH_TOOLTIP_FRAGMENT, TypeWithTooltip} from '../typeexplorer/TypeWithTooltip';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {IconWIP} from '../ui/Icon';
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
  OpLinks,
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
      <SidebarSection title={'Definition'}>
        <Box padding={{vertical: 16, horizontal: 24}}>
          <SidebarSubhead>{isComposite ? 'Graph' : 'Op'}</SidebarSubhead>
          <SidebarTitle>{breakOnUnderscores(definition.name)}</SidebarTitle>
          <OpTypeSignature definition={definition} />
        </Box>
      </SidebarSection>
      {definition.description && (
        <SidebarSection title={'Description'}>
          <Box padding={{vertical: 16, horizontal: 24}}>
            <Description description={definition.description} />
          </Box>
        </SidebarSection>
      )}
      {definition.metadata && Plugin && Plugin.SidebarComponent && (
        <SidebarSection title={'Metadata'}>
          <Box padding={{vertical: 16, horizontal: 24}}>
            <Plugin.SidebarComponent definition={definition} repoAddress={repoAddress} />
          </Box>
        </SidebarSection>
      )}
      {configField && (
        <SidebarSection title={'Config'}>
          <Box padding={{vertical: 16, horizontal: 24}}>
            <ConfigTypeSchema
              type={configField.configType}
              typesInScope={configField.configType.recursiveConfigTypes}
            />
          </Box>
        </SidebarSection>
      )}
      {requiredResources && (
        <SidebarSection title={'Required Resources'}>
          <Box padding={{vertical: 16, horizontal: 24}}>
            {[...requiredResources].sort().map((requirement) => (
              <ResourceContainer key={requirement.resourceKey}>
                <IconWIP name="resource" color={ColorsWIP.Gray700} />
                <ResourceHeader>{requirement.resourceKey}</ResourceHeader>
              </ResourceContainer>
            ))}
          </Box>
        </SidebarSection>
      )}
      <SidebarSection title={'Inputs'}>
        <Box padding={{vertical: 16, horizontal: 24}}>
          {definition.inputDefinitions.map((inputDef, idx) => (
            <SectionItemContainer key={idx}>
              <SectionSmallHeader>{breakOnUnderscores(inputDef.name)}</SectionSmallHeader>
              <TypeWrapper>
                <TypeWithTooltip type={inputDef.type} />
              </TypeWrapper>
              <Description description={inputDef.description} />
              <OpLinks title="Mapped to:" items={inputMappings[inputDef.name]} />
            </SectionItemContainer>
          ))}
        </Box>
      </SidebarSection>
      <SidebarSection title={'Outputs'}>
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
              <OpLinks title="Mapped from:" items={outputMappings[outputDef.name]} />
              <Description description={outputDef.description} />
            </SectionItemContainer>
          ))}
        </Box>
      </SidebarSection>
      {getInvocations && (
        <SidebarSection title={'All Invocations'}>
          <InvocationList
            invocations={getInvocations(definition.name)}
            onClickInvocation={onClickInvocation}
          />
        </SidebarSection>
      )}
    </div>
  );
};

export const SIDEBAR_SOLID_DEFINITION_FRAGMENT = gql`
  fragment SidebarOpDefinitionFragment on ISolidDefinition {
    ...OpTypeSignatureFragment
    __typename
    name
    description
    metadata {
      key
      value
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
  const displayed = showAll ? invocations : invocations.slice(0, DEFAULT_INVOCATIONS_SHOWN);

  return (
    <>
      {displayed.map((invocation, idx) => (
        <Invocation
          key={idx}
          invocation={invocation}
          onClick={() => onClickInvocation(invocation)}
        />
      ))}
      {displayed.length < invocations.length && (
        <ShowAllButton onClick={() => setShowAll(true)}>
          {`Show ${invocations.length - displayed.length} More Invocations`}
        </ShowAllButton>
      )}
    </>
  );
};
