import * as React from 'react';
import gql from 'graphql-tag';
import TypeWithTooltip from './TypeWithTooltip';
import {SidebarSection, SidebarTitle} from './SidebarComponents';
import {SidebarSolidInvocationFragment} from './types/SidebarSolidInvocationFragment';
import {DependencyTable, DependencyRow, DependencyHeaderRow} from './SidebarSolidHelpers';
import {Button} from '@blueprintjs/core';
import {SolidNameOrPath} from './PipelineExplorer';
import {breakOnUnderscores} from './Util';

interface ISidebarSolidInvocationProps {
  solid: SidebarSolidInvocationFragment;
  onEnterCompositeSolid?: (arg: SolidNameOrPath) => void;
}

export class SidebarSolidInvocation extends React.Component<ISidebarSolidInvocationProps> {
  static fragments = {
    SidebarSolidInvocationFragment: gql`
      fragment SidebarSolidInvocationFragment on Solid {
        name
        inputs {
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

      ${TypeWithTooltip.fragments.DagsterTypeWithTooltipFragment}
    `,
  };

  state = {
    showingAllInvocations: false,
  };

  public render() {
    const {solid, onEnterCompositeSolid} = this.props;

    return (
      <div>
        <SidebarSection title={'Invocation'}>
          <SidebarTitle>{breakOnUnderscores(solid.name)}</SidebarTitle>
          <DependencyTable>
            <tbody>
              {solid.inputs.some((o) => o.dependsOn.length) && (
                <DependencyHeaderRow label="Inputs" />
              )}
              {solid.inputs.map(({definition, dependsOn}) =>
                dependsOn.map((source, idx) => (
                  <DependencyRow key={idx} from={source} to={definition.name} />
                )),
              )}
              {solid.outputs.some((o) => o.dependedBy.length) && (
                <DependencyHeaderRow label="Outputs" style={{paddingTop: 15}} />
              )}
              {solid.outputs.map(({definition, dependedBy}) =>
                dependedBy.map((target, idx) => (
                  <DependencyRow key={idx} from={definition.name} to={target} />
                )),
              )}
            </tbody>
          </DependencyTable>
          {onEnterCompositeSolid && (
            <Button
              icon="zoom-in"
              text="Expand Composite"
              style={{marginTop: 15}}
              onClick={() => onEnterCompositeSolid({name: solid.name})}
            />
          )}
        </SidebarSection>
      </div>
    );
  }
}
