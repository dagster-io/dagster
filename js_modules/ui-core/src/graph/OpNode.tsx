import {Icon} from '@dagster-io/ui-components';
import clsx from 'clsx';
import * as React from 'react';

import {COMPUTE_KIND_TAG} from './KindTags';
import {OpIOBox, metadataForIO} from './OpIOBox';
import {IOpTag, OpTags} from './OpTags';
import {OpLayout} from './asyncGraphLayout';
import {Edge, position} from './common';
import {gql} from '../apollo-client';
import styles from './css/OpNode.module.css';
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
      <div
        className={clsx(styles.nodeContainer, dim && styles.dim)}
        onClick={this.handleClick}
        onDoubleClick={this.handleDoubleClick}
        data-testid={testId(definition.name)}
      >
        <div
          className={clsx(styles.highlightBox, selected && styles.highlightBoxSelected)}
          style={{...position(layout.bounds)}}
        />
        {composite && (
          <div
            className={clsx(
              styles.compositeMarker,
              minified && styles.compositeMarkerMinified,
              selected && styles.compositeMarkerSelected,
            )}
            style={{...position(layout.op)}}
          />
        )}

        {invocation?.isDynamicMapped && (
          <div
            className={clsx(styles.dynamicMarker, minified && styles.dynamicMarkerMinified)}
            style={{...position(layout.op)}}
          />
        )}

        {configField && configField.configType.key !== 'Any' && (
          <div
            className={clsx(styles.configMarker, minified && styles.configMarkerMinified)}
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
        <div
          className={clsx(
            styles.nodeBox,
            minified && styles.nodeBoxMinified,
            selected && (minified ? styles.nodeBoxSelectedMinified : styles.nodeBoxSelected),
            !selected &&
              focused &&
              (minified ? styles.nodeBoxFocusedMinified : styles.nodeBoxFocused),
          )}
          style={{...position(layout.op)}}
        >
          <div className={clsx(styles.name, minified && styles.nameMinified)}>
            {!minified && <Icon name="op" size={16} />}
            <div className={styles.label} data-tooltip={label} data-tooltip-style={TOOLTIP_STYLE}>
              {withMiddleTruncation(label, {maxLength: 48})}
            </div>
          </div>
          {!minified && (definition.description || definition.assetNodes.length === 0) && (
            <div className={styles.description}>
              {(definition.description || '').split('\n')[0]}
            </div>
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
      </div>
    );
  }
}

const OpNodeAssociatedAssets = ({nodes}: {nodes: {assetKey: AssetKey}[]}) => {
  const more = nodes.length > 1 ? ` + ${nodes.length - 1} more` : '';
  return (
    <div className={styles.assets}>
      <Icon name="asset" size={16} />
      {/* eslint-disable-next-line @typescript-eslint/no-non-null-assertion */}
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
