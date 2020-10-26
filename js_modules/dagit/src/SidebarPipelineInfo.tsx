import {gql} from '@apollo/client';
import {Colors, Icon} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import styled from 'styled-components/macro';

import {ConfigTypeSchema} from 'src/ConfigTypeSchema';
import {Description} from 'src/Description';
import {
  SectionHeader,
  SectionInner,
  SectionItemContainer,
  SidebarSection,
  SidebarSubhead,
  SidebarTitle,
} from 'src/SidebarComponents';
import {breakOnUnderscores} from 'src/Util';
import {SidebarPipelineInfoFragment} from 'src/types/SidebarPipelineInfoFragment';

const NO_DESCRIPTION = '';

interface ISidebarPipelineInfoProps {
  pipeline: SidebarPipelineInfoFragment;
}

export class SidebarPipelineInfo extends React.Component<ISidebarPipelineInfoProps> {
  static fragments = {
    SidebarPipelineInfoFragment: gql`
      fragment SidebarPipelineInfoFragment on IPipelineSnapshot {
        name
        description
        modes {
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
      }

      ${ConfigTypeSchema.fragments.ConfigTypeSchemaFragment}
    `,
  };

  render() {
    const {pipeline} = this.props;

    return (
      <div>
        <SectionInner>
          <SidebarSubhead>Pipeline</SidebarSubhead>
          <SidebarTitle>{breakOnUnderscores(pipeline.name)}</SidebarTitle>
        </SectionInner>
        <SidebarSection title={'Description'}>
          <Description description={pipeline ? pipeline.description : NO_DESCRIPTION} />
        </SidebarSection>
        <SidebarSection title={'Modes'} collapsedByDefault={true}>
          {pipeline.modes.map((mode) => (
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
          ))}
        </SidebarSection>
      </div>
    );
  }
}

const ContextResourceHeader = styled(SectionHeader)`
  font-size: 13px;
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
  font-size: 13px;
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
