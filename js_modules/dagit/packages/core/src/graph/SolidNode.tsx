import {gql} from '@apollo/client';
import * as React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP} from '../ui/Colors';
import {FontFamily} from '../ui/styles';

import {PipelineColorScale} from './PipelineColorScale';
import {SolidConfigPort} from './SolidConfigPort';
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

const SELECTED_STYLE = {
  stroke: 'rgba(255, 69, 0, 1)',
  fill: 'rgba(255, 69, 0, 0.2)',
  dashed: true,
};
const FOCUSED_STYLE = {
  stroke: 'rgba(59, 141, 227, 1)',
  fill: 'rgba(59, 141, 227, 0.2)',
  dashed: false,
};
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

  public renderSolidCompositeIndicator() {
    const {x, y, width, height} = this.props.layout.solid;
    return (
      <>
        <rect
          x={x - 6}
          y={y - 6}
          width={width + 12}
          height={height + 12}
          fill={PipelineColorScale('solidComposite')}
          stroke="#979797"
          strokeWidth={1}
        />
        <rect
          x={x - 3}
          y={y - 3}
          width={width + 6}
          height={height + 6}
          fill={PipelineColorScale('solidComposite')}
          stroke="#979797"
          strokeWidth={1}
        />
      </>
    );
  }

  public render() {
    const {definition, invocation, layout, dim, focused, selected, minified} = this.props;
    const {metadata} = definition;
    if (!layout) {
      throw new Error(`Layout is missing for ${definition.name}`);
    }
    const {x, y, width, height} = layout.solid;

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
      <div onClick={this.handleClick} onDoubleClick={this.handleDoubleClick}>
        <NodeContainer
          $selected={selected}
          $secondaryHighlight={focused}
          data-tooltip={invocation ? invocation.name : definition.name}
          data-tooltip-style={TOOLTIP_STYLE}
          style={{...position(layout.boundingBox), opacity: dim ? 0.3 : 1}}
        />
        {composite && this.renderSolidCompositeIndicator()}

        {invocation?.isDynamicMapped && (
          <div style={{transform: 'translate(7px, 7px)', background: 'red'}}></div>
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

        <NodeBox style={{...position(layout.solid)}}>
          <Name>{invocation ? invocation.name : definition.name}</Name>
          <Description>{(definition.description || '').split('\n')[0]}</Description>
        </NodeBox>

        {configField && configField.configType.key !== 'Any' ? (
          <SolidConfigPort x={x + width - 33} y={y - 13} minified={minified} />
        ) : null}

        {tags.length > 0 && (
          <SolidTags y={y + height - layout.boundingBox.y} minified={minified} tags={tags} />
        )}
      </div>
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

const NodeContainer = styled.div<{$selected: boolean; $secondaryHighlight: boolean}>`
  border: ${(p) =>
    p.$selected
      ? `2px dashed rgba(255, 69, 0, 1)`
      : p.$secondaryHighlight
      ? `2px solid ${ColorsWIP.Blue500}55`
      : '2px solid transparent'};
  border-radius: 6px;
  background: ${(p) => (p.$selected ? 'rgba(255, 69, 0, 0.2)' : 'transparent')};
`;

const NodeBox = styled.div`
  border: 2px solid #dcd5ca;
  background: #f5f3ef;
  border-radius: 5px;
`;

const Name = styled.div`
  display: flex;
  padding: 4px 8px;
  font-family: ${FontFamily.monospace};
  background: ${ColorsWIP.White};
  border-top-left-radius: 5px;
  border-top-right-radius: 5px;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 600;
`;

const Description = styled.div`
  padding: 4px 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border-top: 1px solid #e6e1d8;
  font-size: 12px;
`;

export const position = ({x, y, width, height}: ILayout) => ({
  left: x,
  top: y,
  width,
  height,
  position: 'absolute' as const,
});
