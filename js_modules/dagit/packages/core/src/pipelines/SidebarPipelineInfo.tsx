import {gql} from '@apollo/client';
import * as React from 'react';

import {useFeatureFlags} from '../app/Flags';
import {breakOnUnderscores} from '../app/Util';

import {Description} from './Description';
import {SectionInner, SidebarSection, SidebarSubhead, SidebarTitle} from './SidebarComponents';
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
      <SectionInner>
        <SidebarSubhead>{flagPipelineModeTuples ? 'Graph' : 'Pipeline'}</SidebarSubhead>
        <SidebarTitle>{breakOnUnderscores(pipeline.name)}</SidebarTitle>
      </SectionInner>
      <SidebarSection title={'Description'}>
        <Description description={pipeline ? pipeline.description : NO_DESCRIPTION} />
      </SidebarSection>
      {!flagPipelineModeTuples && (
        <SidebarSection title={'Modes'} collapsedByDefault={true}>
          {pipeline.modes.map((mode) => (
            <SidebarModeSection key={mode.name} mode={mode} />
          ))}
        </SidebarSection>
      )}
    </div>
  );
};

export const SIDEBAR_PIPELINE_INFO_FRAGMENT = gql`
  fragment SidebarPipelineInfoFragment on IPipelineSnapshot {
    name
    description
    modes {
      id
      ...SidebarModeInfoFragment
    }
  }

  ${SIDEBAR_MODE_INFO_FRAGMENT}
`;
