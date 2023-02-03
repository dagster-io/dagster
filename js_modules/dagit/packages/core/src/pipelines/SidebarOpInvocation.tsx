import {gql} from '@apollo/client';
import {Box, Button, Icon} from '@dagster-io/ui';
import * as React from 'react';

import {CodeLink} from '../app/CodeLink';
import {breakOnUnderscores} from '../app/Util';
import {OpNameOrPath} from '../ops/OpNameOrPath';
import {DAGSTER_TYPE_WITH_TOOLTIP_FRAGMENT} from '../typeexplorer/TypeWithTooltip';

import {SidebarSection, SidebarTitle} from './SidebarComponents';
import {DependencyHeaderRow, DependencyRow, DependencyTable} from './SidebarOpHelpers';
import {SidebarOpInvocationFragment} from './types/SidebarOpInvocation.types';

interface ISidebarOpInvocationProps {
  solid: SidebarOpInvocationFragment;
  onEnterSubgraph?: (arg: OpNameOrPath) => void;
}

export const SidebarOpInvocation: React.FC<ISidebarOpInvocationProps> = (props) => {
  const {solid, onEnterSubgraph} = props;
  const showInputs = solid.inputs.some((o) => o.dependsOn.length);
  const showOutputs = solid.outputs.some((o) => o.dependedBy.length);

  const codeLinkMetadata = solid.definition.metadata.find((m) => m.key === '__code_origin')?.value;
  let codeLink = null;
  if (codeLinkMetadata) {
    const [codeLinkFile, codeLinkLineNumber] = codeLinkMetadata.split(':');
    codeLink = <CodeLink file={codeLinkFile} lineNumber={parseInt(codeLinkLineNumber)} />;
  }
  return (
    <div>
      <SidebarSection title="Invocation">
        <Box padding={{vertical: 16, horizontal: 24}}>
          <SidebarTitle>{breakOnUnderscores(solid.name)}</SidebarTitle>
          {codeLink}
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

export const SIDEBAR_OP_INVOCATION_FRAGMENT = gql`
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
    definition {
      metadata {
        key
        value
      }
    }
  }

  ${DAGSTER_TYPE_WITH_TOOLTIP_FRAGMENT}
`;
