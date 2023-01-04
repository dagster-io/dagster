import {Box, Button, Icon} from '@dagster-io/ui';
import * as React from 'react';

import {breakOnUnderscores} from '../app/Util';
import {graphql} from '../graphql';
import {SidebarOpInvocationFragmentFragment} from '../graphql/graphql';
import {OpNameOrPath} from '../ops/OpNameOrPath';

import {SidebarSection, SidebarTitle} from './SidebarComponents';
import {DependencyHeaderRow, DependencyRow, DependencyTable} from './SidebarOpHelpers';

interface ISidebarOpInvocationProps {
  solid: SidebarOpInvocationFragmentFragment;
  onEnterSubgraph?: (arg: OpNameOrPath) => void;
}

export const SidebarOpInvocation: React.FC<ISidebarOpInvocationProps> = (props) => {
  const {solid, onEnterSubgraph} = props;
  const showInputs = solid.inputs.some((o) => o.dependsOn.length);
  const showOutputs = solid.outputs.some((o) => o.dependedBy.length);

  return (
    <div>
      <SidebarSection title="Invocation">
        <Box padding={{vertical: 16, horizontal: 24}}>
          <SidebarTitle>{breakOnUnderscores(solid.name)}</SidebarTitle>
          {showInputs || showOutputs ? (
            <DependencyTable>
              <tbody>
                {showInputs ? (
                  <>
                    <DependencyHeaderRow label="Inputs" />
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
                  </>
                ) : null}
                {showOutputs ? (
                  <>
                    <DependencyHeaderRow label="Outputs" />
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
                  </>
                ) : null}
              </tbody>
            </DependencyTable>
          ) : null}
          {onEnterSubgraph && (
            <Box margin={{top: 12}}>
              <Button
                icon={<Icon name="zoom_in" />}
                onClick={() => onEnterSubgraph({name: solid.name})}
              >
                Expand graph
              </Button>
            </Box>
          )}
        </Box>
      </SidebarSection>
    </div>
  );
};

export const SIDEBAR_OP_INVOCATION_FRAGMENT = graphql(`
  fragment SidebarOpInvocationFragment on Solid {
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
`);
