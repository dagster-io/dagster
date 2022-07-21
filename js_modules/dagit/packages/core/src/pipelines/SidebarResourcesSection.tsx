import {gql} from '@apollo/client';
import {Colors, ConfigTypeSchema, Icon, IconWrapper, Box} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import {CONFIG_TYPE_SCHEMA_FRAGMENT} from '../typeexplorer/ConfigTypeSchema';

import {Description} from './Description';
import {SectionHeader, SectionItemContainer} from './SidebarComponents';
import {SidebarResourcesSectionFragment} from './types/SidebarResourcesSectionFragment';

const NO_DESCRIPTION = '';

export const SidebarResourcesSection: React.FC<{
  mode: SidebarResourcesSectionFragment;
  showModeName?: boolean;
}> = ({mode, showModeName}) => {
  return (
    <SectionItemContainer key={mode.name}>
      {showModeName && (
        <Box padding={{bottom: 16}}>
          <SectionHeader>{mode.name}</SectionHeader>
          <Description description={mode.description || NO_DESCRIPTION} />
        </Box>
      )}
      <Box flex={{direction: 'column', gap: 16}}>
        {[...mode.resources, ...mode.loggers].map((resource) => (
          <ContextResourceContainer key={resource.name}>
            <Icon name="resource" color={Colors.Gray700} />
            <div>
              <ContextResourceHeader>{resource.name}</ContextResourceHeader>
              <Description description={resource.description || NO_DESCRIPTION} />
              {resource.configField && (
                <ConfigTypeSchema
                  type={resource.configField.configType}
                  typesInScope={resource.configField.configType.recursiveConfigTypes}
                />
              )}
            </div>
          </ContextResourceContainer>
        ))}
      </Box>
    </SectionItemContainer>
  );
};

export const SIDEBAR_RESOURCES_SECTION_FRAGMENT = gql`
  fragment SidebarResourcesSectionFragment on Mode {
    id
    name
    description
    resources {
      name
      description
      configField {
        configType {
          ...ConfigTypeSchemaFragment
          recursiveConfigTypes {
            ...ConfigTypeSchemaFragment
          }
        }
      }
    }
    loggers {
      name
      description
      configField {
        configType {
          ...ConfigTypeSchemaFragment
          recursiveConfigTypes {
            ...ConfigTypeSchemaFragment
          }
        }
      }
    }
  }

  ${CONFIG_TYPE_SCHEMA_FRAGMENT}
`;

const ContextResourceHeader = styled(SectionHeader)`
  font-size: 16px;
  margin: 4px 0;
`;

const ContextResourceContainer = styled.div`
  display: flex;
  align-items: flex-start;

  & h4 {
    margin-top: -2px;
  }
  & ${IconWrapper} {
    margin-right: 8px;
  }
`;
