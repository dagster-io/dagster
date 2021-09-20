import {gql} from '@apollo/client';
import {Colors, Icon} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import styled from 'styled-components/macro';

import {ConfigTypeSchema, CONFIG_TYPE_SCHEMA_FRAGMENT} from '../typeexplorer/ConfigTypeSchema';

import {Description} from './Description';
import {SectionHeader, SectionItemContainer} from './SidebarComponents';
import {SidebarModeInfoFragment} from './types/SidebarModeInfoFragment';

const NO_DESCRIPTION = '';

export const SidebarModeSection: React.FunctionComponent<{
  mode: SidebarModeInfoFragment;
}> = ({mode}) => {
  return (
    <SectionItemContainer key={mode.name}>
      <SectionHeader>{mode.name}</SectionHeader>
      <Description description={mode.description || NO_DESCRIPTION} />
      {mode.resources.map((resource) => (
        <ContextResourceContainer key={resource.name}>
          <Icon iconSize={14} icon={IconNames.LAYERS} color={Colors.DARK_GRAY2} />
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
      {mode.loggers.map((logger) => (
        <ContextLoggerContainer key={logger.name}>
          <Icon iconSize={14} icon={IconNames.LAYERS} color={Colors.DARK_GRAY2} />
          <div>
            <ContextLoggerHeader>{logger.name}</ContextLoggerHeader>
            <Description description={logger.description || NO_DESCRIPTION} />
            {logger.configField && (
              <ConfigTypeSchema
                type={logger.configField.configType}
                typesInScope={logger.configField.configType.recursiveConfigTypes}
              />
            )}
          </div>
        </ContextLoggerContainer>
      ))}
    </SectionItemContainer>
  );
};

export const SIDEBAR_MODE_INFO_FRAGMENT = gql`
  fragment SidebarModeInfoFragment on Mode {
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
  padding-top: 15px;
  & .bp3-icon {
    padding-top: 7px;
    padding-right: 10px;
  }
`;

const ContextLoggerHeader = styled(SectionHeader)`
  font-size: 16px;
  margin: 4px 0;
`;

const ContextLoggerContainer = styled.div`
  display: flex;
  align-items: flex-start;
  padding-top: 15px;
  & .bp3-icon {
    padding-top: 7px;
    padding-right: 10px;
  }
`;
