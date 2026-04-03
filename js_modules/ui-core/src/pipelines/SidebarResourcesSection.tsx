import {Box, Colors, ConfigTypeSchema, Icon} from '@dagster-io/ui-components';

import {Description} from './Description';
import {SectionHeader, SectionItemContainer} from './SidebarComponents';
import {gql} from '../apollo-client';
import {SidebarResourcesSectionFragment} from './types/SidebarResourcesSection.types';
import {CONFIG_TYPE_SCHEMA_FRAGMENT} from '../typeexplorer/ConfigTypeSchema';
import styles from './css/SidebarResourcesSection.module.css';

const NO_DESCRIPTION = '';

export const SidebarResourcesSection = ({
  mode,
  showModeName,
}: {
  mode: SidebarResourcesSectionFragment;
  showModeName?: boolean;
}) => {
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
          <div className={styles.contextResourceContainer} key={resource.name}>
            <Icon name="resource" color={Colors.accentGray()} />
            <div>
              <SectionHeader className={styles.contextResourceHeader}>
                {resource.name}
              </SectionHeader>
              <Description description={resource.description || NO_DESCRIPTION} />
              {resource.configField && (
                <ConfigTypeSchema
                  type={resource.configField.configType}
                  typesInScope={resource.configField.configType.recursiveConfigTypes}
                />
              )}
            </div>
          </div>
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
