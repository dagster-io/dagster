import {Colors, FontFamily, Icon} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {COMPUTE_KIND_TAG} from './KindTags';
import {OpIOBox, metadataForIO} from './OpIOBox';
import {IOpTag, OpTags} from './OpTags';
import {OpLayout} from './asyncGraphLayout';
import {Edge, position} from './common';
import {gql} from '../apollo-client';
import {OpNodeDefinitionFragment, OpNodeInvocationFragment} from './types/OpNode.types';
import {withMiddleTruncation} from '../app/Util';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {AssetKey} from '../assets/types';
import {testId} from '../testing/testId';

interface IOpNodeProps {
  layout: OpLayout;
  invocation?: OpNodeInvocationFragment;
  definition: OpNodeDefinitionFragment;
  highlightedEdges: Edge[];
  minified: boolean;
  selected: boolean;
  focused: boolean;
  dim: boolean;
  onClick: () => void;
  onDoubleClick: () => void;
  onEnterComposite: () => void;
  onHighlightEdges: (edges: Edge[]) => void;
  isExternal?: boolean;
}

const TOOLTIP_STYLE = JSON.stringify({
  top: -20,
  left: 5,
});

export class OpNode extends React.Component<IOpNodeProps> {
  shouldComponentUpdate(prevProps: IOpNodeProps) {
    if (prevProps.dim !== this.props.dim) {
      return true;
    }
    if (prevProps.selected !== this.props.selected) {
      return true;
    }
    if (prevProps.focused !== this.props.focused) {
      return true;
    }
    if (prevProps.minified !== this.props.minified) {
      return true;
    }
    if (prevProps.highlightedEdges !== this.props.highlightedEdges) {
      return true;
    }
    if (prevProps.layout !== this.props.layout) {
      return true;
    }
    if (
      (prevProps.invocation && prevProps.invocation.name) !==
      (this.props.invocation && this.props.invocation.name)
    ) {
      return true;
    }
    return false;
  }

  handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    this.props.onClick();
  };

  handleDoubleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    this.props.onDoubleClick();
  };

  handleEnterComposite = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    this.props.onEnterComposite();
  };

  handleKindClicked = (e: React.MouseEvent) => {
    this.handleClick(e);
    window.requestAnimationFrame(() => document.dispatchEvent(new Event('show-kind-info')));
  };

  public render() {
    const {definition, invocation, layout, dim, focused, selected, minified, isExternal} =
      this.props;
    const {metadata} = definition;
    if (!layout) {
      throw new Error(`Layout is missing for ${definition.name}`);
    }

    let configField = null;
    if (definition.__typename === 'SolidDefinition') {
      configField = definition.configField;
    }

    const tags: IOpTag[] = [];

    const kind = metadata.find((m) => m.key === COMPUTE_KIND_TAG);
    const composite = definition.__typename === 'CompositeSolidDefinition';

    if (kind) {
      tags.push({label: kind.value, onClick: this.handleKindClicked});
    }
    if (composite) {
      tags.push({label: 'Expand', onClick: this.handleEnterComposite});
    }

    const label = invocation ? invocation.name : definition.name;

    return (
      <NodeContainer
        $minified={minified}
        $selected={selected}
        $secondaryHighlight={focused}
        $dim={dim}
        onClick={this.handleClick}
        onDoubleClick={this.handleDoubleClick}
        data-testid={testId(definition.name)}
      >
        <div className="highlight-box" style={{...position(layout.bounds)}} />
        {composite && <div className="composite-marker" style={{...position(layout.op)}} />}

        {invocation?.isDynamicMapped && (
          <div className="dynamic-marker" style={{...position(layout.op)}} />
        )}

        {configField && configField.configType.key !== 'Any' && (
          <div
            className="config-marker"
            style={{left: layout.op.x + layout.op.width, top: layout.op.y}}
          >
            {minified ? 'C' : 'Config'}
          </div>
        )}
        {!isExternal && (
          <div>
            {definition.inputDefinitions.map((item, idx) => (
              <OpIOBox
                {...this.props}
                {...metadataForIO(item, invocation)}
                key={idx}
                item={item}
                layoutInfo={layout.inputs[item.name]}
                colorKey="input"
              />
            ))}
          </div>
        )}
        <div className="node-box" style={{...position(layout.op)}}>
          <div className="name">
            {!minified && <Icon name="op" size={16} />}
            <div className="label" data-tooltip={label} data-tooltip-style={TOOLTIP_STYLE}>
              {withMiddleTruncation(label, {maxLength: 48})}
            </div>
          </div>
          {!minified && (definition.description || definition.assetNodes.length === 0) && (
            <div className="description">{(definition.description || '').split('\n')[0]}</div>
          )}
          {!minified && definition.assetNodes.length > 0 && (
            <OpNodeAssociatedAssets nodes={definition.assetNodes} />
          )}
        </div>

        {tags.length > 0 && (
          <OpTags
            tags={tags}
            style={{
              left: layout.op.x + layout.op.width,
              top: layout.op.y + layout.op.height,
              transform: 'translate(-100%, 3px)',
            }}
          />
        )}
        {!isExternal && (
          <div>
            {definition.outputDefinitions.map((item, idx) => (
              <OpIOBox
                {...this.props}
                {...metadataForIO(item, invocation)}
                key={idx}
                item={item}
                layoutInfo={layout.outputs[item.name]}
                colorKey="output"
              />
            ))}
          </div>
        )}
      </NodeContainer>
    );
  }
}

const OpNodeAssociatedAssets = ({nodes}: {nodes: {assetKey: AssetKey}[]}) => {
  const more = nodes.length > 1 ? ` + ${nodes.length - 1} more` : '';
  return (
    <div className="assets">
      <Icon name="asset" size={16} />
      {withMiddleTruncation(displayNameForAssetKey(nodes[0]!.assetKey), {
        maxLength: 48 - more.length,
      })}
      {more}
    </div>
  );
};

export const OP_NODE_INVOCATION_FRAGMENT = gql`
  fragment OpNodeInvocationFragment on Solid {
    name
    isDynamicMapped
    inputs {
      definition {
        name
      }
      isDynamicCollect
      dependsOn {
        definition {
          name
          type {
            displayName
          }
        }
        solid {
          name
        }
      }
    }
    outputs {
      definition {
        name
      }
      dependedBy {
        solid {
          name
        }
        definition {
          name
          type {
            displayName
          }
        }
      }
    }
  }
`;

export const OP_NODE_DEFINITION_FRAGMENT = gql`
  fragment OpNodeDefinitionFragment on ISolidDefinition {
    name
    description
    metadata {
      key
      value
    }
    assetNodes {
      id
      assetKey {
        path
      }
    }
    inputDefinitions {
      ...OpNodeInputDefinition
    }
    outputDefinitions {
      ...OpNodeOutputDefinition
    }
    ... on SolidDefinition {
      configField {
        configType {
          key
          description
        }
      }
    }
    ... on CompositeSolidDefinition {
      id
      inputMappings {
        definition {
          name
        }
        mappedInput {
          definition {
            name
          }
          solid {
            name
          }
        }
      }
      outputMappings {
        definition {
          name
        }
        mappedOutput {
          definition {
            name
          }
          solid {
            name
          }
        }
      }
    }
  }

  fragment OpNodeInputDefinition on InputDefinition {
    name
    type {
      displayName
    }
  }

  fragment OpNodeOutputDefinition on OutputDefinition {
    name
    isDynamic
    type {
      displayName
    }
  }
`;

const NodeHighlightColors = {
  Border: Colors.accentBlue(),
  Background: Colors.backgroundBlue(),
};

const NodeContainer = styled.div<{
  $minified: boolean;
  $selected: boolean;
  $secondaryHighlight: boolean;
  $dim: boolean;
}>`
  opacity: ${({$dim}) => ($dim ? 0.3 : 1)};
  pointer-events: auto;
  user-select: none;
  cursor: default;

  .highlight-box {
    border-radius: 13px;
    background: ${(p) => (p.$selected ? NodeHighlightColors.Background : 'transparent')};
  }
  .node-box {
    border: ${(p) =>
      p.$selected
        ? `2px dashed ${NodeHighlightColors.Border}`
        : p.$secondaryHighlight
          ? `2px solid ${Colors.accentBlue()}55`
          : `2px solid ${Colors.keylineDefault()}`};

    border-width: ${(p) => (p.$minified ? '3px' : '2px')};
    border-radius: 8px;
    background: ${(p) => (p.$minified ? Colors.backgroundLight() : Colors.backgroundDefault())};
  }
  .composite-marker {
    outline: ${(p) => (p.$minified ? '3px' : '2px')} solid
      ${(p) => (p.$selected ? 'transparent' : Colors.accentYellow())};
    outline-offset: ${(p) => (p.$minified ? '5px' : '3px')};
    border-radius: 3px;
  }
  .dynamic-marker {
    transform: translate(-5px, -5px);
    border: ${(p) => (p.$minified ? '3px' : '2px')} solid ${Colors.keylineDefault()};
    border-radius: 8px;
  }
  .config-marker {
    position: absolute;
    transform: ${(p) => (p.$minified ? ' translate(-100%, -28px)' : ' translate(-100%, -21px)')};
    font-size: ${(p) => (p.$minified ? '24px' : '12px')};
    font-family: ${FontFamily.monospace};
    font-weight: 700;
    opacity: 0.5;
  }
  .name {
    display: flex;
    gap: 5px;
    padding: 4px ${(p) => (p.$minified ? '8px' : '3px')};
    font-size: ${(p) => (p.$minified ? '32px' : '14px')};
    font-family: ${FontFamily.monospace};
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    align-items: center;
    font-weight: 600;
    .label {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
  .assets {
    padding: 0 4px;
    white-space: nowrap;
    line-height: 22px;
    height: 22px;
    overflow: hidden;
    text-overflow: ellipsis;
    background: ${Colors.backgroundLighter()};
    font-size: 12px;
    display: flex;
    gap: 4px;
    align-items: center;
  }
  .description {
    padding: 0 8px;
    white-space: nowrap;
    line-height: 22px;
    height: 22px;
    overflow: hidden;
    text-overflow: ellipsis;
    background: ${Colors.backgroundLighter()};
    border-top: ${Colors.keylineDefault()} 1px solid;

    /* 6px because it's inside a bordered box with a 2px line at our standard 8px radius */
    border-bottom-left-radius: 6px;
    border-bottom-right-radius: 6px;
    font-size: 12px;
  }
`;
