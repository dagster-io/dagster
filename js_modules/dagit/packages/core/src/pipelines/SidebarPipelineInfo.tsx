import {gql} from '@apollo/client';
import * as React from 'react';

import {breakOnUnderscores} from '../app/Util';
import {Box} from '../ui/Box';

import {Description} from './Description';
import {SidebarSection, SidebarSubhead, SidebarTitle} from './SidebarComponents';
import {SidebarModeSection, SIDEBAR_MODE_INFO_FRAGMENT} from './SidebarModeSection';
import {SidebarOpContainerInfoFragment} from './types/SidebarOpContainerInfoFragment';

const NO_DESCRIPTION = '';

interface ISidebarOpContainerInfoProps {
  isGraph: boolean;
  pipeline: SidebarOpContainerInfoFragment;
}

export const SidebarOpContainerInfo: React.FC<ISidebarOpContainerInfoProps> = ({
  isGraph,
  pipeline,
}) => {
  return (
    <div>
      <Box padding={{vertical: 16, horizontal: 24}}>
        <SidebarSubhead>{isGraph ? 'Graph' : 'Pipeline'}</SidebarSubhead>
        <SidebarTitle>{breakOnUnderscores(pipeline.name)}</SidebarTitle>
      </Box>
      <SidebarSection title="Description">
        <Box padding={{vertical: 16, horizontal: 24}}>
          <Description description={pipeline ? pipeline.description : NO_DESCRIPTION} />
        </Box>
      </SidebarSection>
      {!isGraph && (
        <SidebarSection title="Modes" collapsedByDefault={true}>
          <Box padding={{vertical: 16, horizontal: 24}}>
            {pipeline.modes.map((mode) => (
              <SidebarModeSection key={mode.name} mode={mode} />
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
      ...SidebarModeInfoFragment
    }
  }

  ${SIDEBAR_MODE_INFO_FRAGMENT}
`;
