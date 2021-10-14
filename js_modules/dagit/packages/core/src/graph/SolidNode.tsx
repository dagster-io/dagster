import {gql} from '@apollo/client';
import * as React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP} from '../ui/Colors';
import {IconWIP} from '../ui/Icon';
import {FontFamily} from '../ui/styles';

import {SolidIOBox, metadataForIO} from './SolidIOBox';
import {SolidTags, ISolidTag} from './SolidTags';
import {IFullSolidLayout, ILayout} from './getFullSolidLayout';
import {Edge} from './highlighting';
import {SolidNodeDefinitionFragment} from './types/SolidNodeDefinitionFragment';
import {SolidNodeInvocationFragment} from './types/SolidNodeInvocationFragment';

interface ISolidNodeProps {
  layout: IFullSolidLayout;
  invocation?: SolidNodeInvocationFragment;
  definition: SolidNodeDefinitionFragment;
  highlightedEdges: Edge[];
  minified: boolean;
  selected: boolean;
  focused: boolean;
  dim: boolean;
  onClick: () => void;
  onDoubleClick: () => void;
  onEnterComposite: () => void;
  onHighlightEdges: (edges: Edge[]) => void;
}

const TOOLTIP_STYLE = JSON.stringify({
  top: -20,
  left: 5,
});

export class SolidNode extends React.Component<ISolidNodeProps> {
  shouldComponentUpdate(prevProps: ISolidNodeProps) {
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
    const {definition, invocation, layout, dim, focused, selected, minified} = this.props;
    const {metadata} = definition;
    if (!layout) {
      throw new Error(`Layout is missing for ${definition.name}`);
    }

    let configField = null;
    if (definition.__typename === 'SolidDefinition') {
      configField = definition.configField;
    }

    const tags: ISolidTag[] = [];

    const kind = metadata.find((m) => m.key === 'kind');
    const composite = definition.__typename === 'CompositeSolidDefinition';

    if (kind) {
      tags.push({label: kind.value, onClick: this.handleKindClicked});
    }
    if (composite) {
      tags.push({label: 'Expand', onClick: this.handleEnterComposite});
    }

    return (
      <NodeContainer
        $minified={minified}
        $selected={selected}
        $secondaryHighlight={focused}
        $dim={dim}
        onClick={this.handleClick}
        onDoubleClick={this.handleDoubleClick}
      >
        <div className="highlight-box" style={{...position(layout.boundingBox)}} />
        {composite && <div className="composite-marker" style={{...position(layout.solid)}} />}

        {invocation?.isDynamicMapped && (
          <div className="dynamic-marker" style={{...position(layout.solid)}} />
        )}

        {configField && configField.configType.key !== 'Any' && (
          <div
            className="config-marker"
            style={{left: layout.solid.x + layout.solid.width, top: layout.solid.y}}
          >
            {minified ? 'C' : 'Config'}
          </div>
        )}

        {definition.inputDefinitions.map((item, idx) => (
          <SolidIOBox
            {...this.props}
            {...metadataForIO(item, invocation)}
            key={idx}
            item={item}
            style={{...position(layout.inputs[item.name].layout)}}
            colorKey="input"
          />
        ))}

        {definition.outputDefinitions.map((item, idx) => (
          <SolidIOBox
            {...this.props}
            {...metadataForIO(item, invocation)}
            key={idx}
            item={item}
            style={{...position(layout.outputs[item.name].layout)}}
            colorKey="output"
          />
        ))}

        <div className="node-box" style={{...position(layout.solid)}}>
          <div
            className="name"
            data-tooltip={invocation ? invocation.name : definition.name}
            data-tooltip-style={TOOLTIP_STYLE}
          >
            {!minified && <IconWIP name="op" size={16} />}
            <div className="label">{invocation ? invocation.name : definition.name}</div>
          </div>
          {!minified && (
            <div className="description">{(definition.description || '').split('\n')[0]}</div>
          )}
        </div>

        {tags.length > 0 && (
          <SolidTags
            style={{
              left: layout.solid.x + layout.solid.width,
              top: layout.solid.y + layout.solid.height,
              transform: 'translate(-100%, 3px)',
            }}
            minified={minified}
            tags={tags}
          />
        )}
      </NodeContainer>
    );
  }
}

export const SOLID_NODE_INVOCATION_FRAGMENT = gql`
  fragment SolidNodeInvocationFragment on Solid {
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

export const SOLID_NODE_DEFINITION_FRAGMENT = gql`
  fragment SolidNodeDefinitionFragment on ISolidDefinition {
    __typename
    name
    description
    metadata {
      key
      value
    }
    inputDefinitions {
      name
      type {
        displayName
      }
    }
    outputDefinitions {
      name
      isDynamic
      type {
        displayName
      }
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
`;

const NodeContainer = styled.div<{
  $minified: boolean;
  $selected: boolean;
  $secondaryHighlight: boolean;
  $dim: boolean;
}>`
  opacity: ${({$dim}) => ($dim ? 0.3 : 1)};

  .highlight-box {
    border: ${(p) =>
      p.$selected
        ? `2px dashed rgba(255, 69, 0, 1)`
        : p.$secondaryHighlight
        ? `2px solid ${ColorsWIP.Blue500}55`
        : '2px solid transparent'};
    border-radius: 6px;
    background: ${(p) => (p.$selected ? 'rgba(255, 69, 0, 0.2)' : 'transparent')};
  }
  .node-box {
    border: 2px solid #dcd5ca;
    border-width: ${(p) => (p.$minified ? '3px' : '2px')};
    border-radius: 5px;
    background: ${(p) => (p.$minified ? ColorsWIP.Gray50 : ColorsWIP.White)};
  }
  .composite-marker {
    outline: ${(p) => (p.$minified ? '3px' : '2px')} solid
      ${(p) => (p.$selected ? 'transparent' : ColorsWIP.Yellow200)};
    outline-offset: ${(p) => (p.$minified ? '5px' : '3px')};
    border-radius: 3px;
  }
  .dynamic-marker {
    transform: translate(-5px, -5px);
    border: ${(p) => (p.$minified ? '3px' : '2px')} solid #dcd5ca;
    border-radius: 3px;
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
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    align-items: center;
    font-weight: 600;
    .label {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
  .description {
    padding: 0 8px;
    white-space: nowrap;
    line-height: 22px;
    height: 22px;
    overflow: hidden;
    text-overflow: ellipsis;
    background: #f5f3ef;
    border-top: 1px solid #e6e1d8;
    border-bottom-left-radius: 5px;
    border-bottom-right-radius: 5px;
    font-size: 12px;
  }
`;

export const position = ({x, y, width, height}: ILayout) => ({
  left: x,
  top: y,
  width,
  height,
  position: 'absolute' as const,
});
