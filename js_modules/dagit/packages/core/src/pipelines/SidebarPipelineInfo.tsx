import {gql} from '@apollo/client';
import * as React from 'react';

import {useFeatureFlags} from '../app/Flags';
import {breakOnUnderscores} from '../app/Util';
import {Box} from '../ui/Box';

import {Description} from './Description';
import {SidebarSection, SidebarSubhead, SidebarTitle} from './SidebarComponents';
import {SidebarModeSection, SIDEBAR_MODE_INFO_FRAGMENT} from './SidebarModeSection';
import {SidebarPipelineInfoFragment} from './types/SidebarPipelineInfoFragment';

const NO_DESCRIPTION = '';

interface ISidebarPipelineInfoProps {
  pipeline: SidebarPipelineInfoFragment;
}

export const SidebarPipelineInfo: React.FC<ISidebarPipelineInfoProps> = ({pipeline}) => {
  const {flagPipelineModeTuples} = useFeatureFlags();
  return (
    <div>
      <Box padding={12}>
        <SidebarSubhead>{flagPipelineModeTuples ? 'Graph' : 'Pipeline'}</SidebarSubhead>
        <SidebarTitle>{breakOnUnderscores(pipeline.name)}</SidebarTitle>
      </Box>
      <SidebarSection title={'Description'}>
        <Box padding={12}>
          <Description description={pipeline ? pipeline.description : NO_DESCRIPTION} />
        </Box>
      </SidebarSection>
      {!flagPipelineModeTuples && (
        <SidebarSection title={'Modes'} collapsedByDefault={true}>
          <Box padding={12}>
            {pipeline.modes.map((mode) => (
              <SidebarModeSection key={mode.name} mode={mode} />
            ))}
          </Box>
        </SidebarSection>
      )}
    </div>
  );
};

export const SIDEBAR_PIPELINE_INFO_FRAGMENT = gql`
  fragment SidebarPipelineInfoFragment on IPipelineSnapshot {
    name
    description
    graphName
    modes {
      id
      ...SidebarModeInfoFragment
    }
  }

  ${SIDEBAR_MODE_INFO_FRAGMENT}
`;
