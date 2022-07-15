import {gql} from '@apollo/client';
import {Box} from '@dagster-io/ui';
import * as React from 'react';

import {breakOnUnderscores} from '../app/Util';

import {Description} from './Description';
import {SidebarSection, SidebarSubhead, SidebarTitle} from './SidebarComponents';
import {
  SidebarResourcesSection,
  SIDEBAR_RESOURCES_SECTION_FRAGMENT,
} from './SidebarResourcesSection';
import {SidebarOpContainerInfoFragment} from './types/SidebarOpContainerInfoFragment';

const NO_DESCRIPTION = '';

interface ISidebarOpContainerInfoProps {
  isGraph: boolean;
  container: SidebarOpContainerInfoFragment;
}

export const SidebarOpContainerInfo: React.FC<ISidebarOpContainerInfoProps> = ({
  isGraph,
  container,
}) => {
  return (
    <div>
      <Box padding={{vertical: 16, horizontal: 24}}>
        <SidebarSubhead>{isGraph ? 'Graph' : 'Pipeline'}</SidebarSubhead>
        <SidebarTitle>{breakOnUnderscores(container.name)}</SidebarTitle>
      </Box>
      <SidebarSection title="Description">
        <Box padding={{vertical: 16, horizontal: 24}}>
          <Description description={container ? container.description : NO_DESCRIPTION} />
        </Box>
      </SidebarSection>
      {!isGraph && (
        <SidebarSection title="Modes" collapsedByDefault={true}>
          <Box padding={{vertical: 16, horizontal: 24}}>
            {container.modes.map((mode) => (
              <SidebarResourcesSection key={mode.name} mode={mode} isGraph={false} />
            ))}
          </Box>
        </SidebarSection>
      )}
    </div>
  );
};

export const SIDEBAR_OP_CONTAINER_INFO_FRAGMENT = gql`
  fragment SidebarOpContainerInfoFragment on SolidContainer {
    id
    name
    description
    modes {
      id
      ...SidebarResourcesSectionFragment
    }
  }

  ${SIDEBAR_RESOURCES_SECTION_FRAGMENT}
`;
