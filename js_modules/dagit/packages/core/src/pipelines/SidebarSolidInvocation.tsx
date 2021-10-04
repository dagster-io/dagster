import {gql} from '@apollo/client';
import * as React from 'react';

import {breakOnUnderscores} from '../app/Util';
import {SolidNameOrPath} from '../solids/SolidNameOrPath';
import {DAGSTER_TYPE_WITH_TOOLTIP_FRAGMENT} from '../typeexplorer/TypeWithTooltip';
import {Box} from '../ui/Box';
import {ButtonWIP} from '../ui/Button';
import {IconWIP} from '../ui/Icon';

import {SidebarSection, SidebarTitle} from './SidebarComponents';
import {DependencyHeaderRow, DependencyRow, DependencyTable} from './SidebarSolidHelpers';
import {SidebarSolidInvocationFragment} from './types/SidebarSolidInvocationFragment';

interface ISidebarSolidInvocationProps {
  solid: SidebarSolidInvocationFragment;
  onEnterCompositeSolid?: (arg: SolidNameOrPath) => void;
}

export const SidebarSolidInvocation: React.FC<ISidebarSolidInvocationProps> = (props) => {
  const {solid, onEnterCompositeSolid} = props;
  return (
    <div>
      <SidebarSection title={'Invocation'}>
        <Box padding={12}>
          <SidebarTitle>{breakOnUnderscores(solid.name)}</SidebarTitle>
          <DependencyTable>
            <tbody>
              {solid.inputs.some((o) => o.dependsOn.length) && (
                <DependencyHeaderRow label="Inputs" />
              )}
              {solid.inputs.map(({definition, dependsOn, isDynamicCollect}) =>
                dependsOn.map((source, idx) => (
                  <DependencyRow
                    key={idx}
                    from={source}
                    to={definition.name}
                    isDynamic={isDynamicCollect}
                  />
                )),
              )}
              {solid.outputs.some((o) => o.dependedBy.length) && (
                <DependencyHeaderRow label="Outputs" style={{paddingTop: 15}} />
              )}
              {solid.outputs.map(({definition, dependedBy}) =>
                dependedBy.map((target, idx) => (
                  <DependencyRow
                    key={idx}
                    from={definition.name}
                    to={target}
                    isDynamic={definition.isDynamic}
                  />
                )),
              )}
            </tbody>
          </DependencyTable>
          {onEnterCompositeSolid && (
            <Box margin={{top: 12}}>
              <ButtonWIP
                icon={<IconWIP name="zoom_in" />}
                onClick={() => onEnterCompositeSolid({name: solid.name})}
              >
                Expand composite
              </ButtonWIP>
            </Box>
          )}
        </Box>
      </SidebarSection>
    </div>
  );
};

export const SIDEBAR_SOLID_INVOCATION_FRAGMENT = gql`
  fragment SidebarSolidInvocationFragment on Solid {
    name
    inputs {
      isDynamicCollect
      definition {
        name
        description
        type {
          ...DagsterTypeWithTooltipFragment
        }
      }
      dependsOn {
        definition {
          name
        }
        solid {
          name
        }
      }
    }
    outputs {
      definition {
        name
        description
        isDynamic
        type {
          ...DagsterTypeWithTooltipFragment
        }
      }
      dependedBy {
        definition {
          name
        }
        solid {
          name
        }
      }
    }
  }

  ${DAGSTER_TYPE_WITH_TOOLTIP_FRAGMENT}
`;
