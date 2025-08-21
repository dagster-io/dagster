import {Colors, FontFamily} from '@dagster-io/ui-components';
import styled from 'styled-components';

import {Edge, isHighlighted, position} from './common';
import {OpLayoutIO} from './layout';
import {
  OpNodeDefinitionFragment,
  OpNodeInputDefinitionFragment,
  OpNodeInvocationFragment,
  OpNodeOutputDefinitionFragment,
} from './types/OpNode.types';
import {DEFAULT_RESULT_NAME, titleOfIO} from '../app/titleOfIO';

export const PARENT_IN = 'PARENT_IN';
export const PARENT_OUT = 'PARENT_OUT';

interface OpIORenderMetadata {
  edges: Edge[];
  jumpTargetOp: string | null;
  title: string;
}

interface OpIOBoxProps extends OpIORenderMetadata {
  colorKey: 'input' | 'output';
  item: OpNodeInputDefinitionFragment | OpNodeOutputDefinitionFragment;
  layoutInfo: OpLayoutIO | undefined;

  // Passed through from Solid props
  minified: boolean;
  highlightedEdges: Edge[];
  onDoubleClick: (opName: string) => void;
  onHighlightEdges: (edges: Edge[]) => void;
}

export const OpIOBox = ({
  minified,
  title,
  jumpTargetOp,
  edges,
  highlightedEdges,
  colorKey,
  item,
  layoutInfo,
  onDoubleClick,
  onHighlightEdges,
}: OpIOBoxProps) => {
  if (!layoutInfo) {
    return null;
  }
  const {name, type} = item;
  const highlighted = edges.some((e) => isHighlighted(highlightedEdges, e));

  return (
    <OpIOContainer
      title={title}
      style={{...position(layoutInfo.layout), width: 'initial'}}
      onMouseEnter={() => onHighlightEdges(edges)}
      onMouseLeave={() => onHighlightEdges([])}
      onClick={(e) => {
        if (jumpTargetOp) {
          onDoubleClick(jumpTargetOp);
        }
        e.stopPropagation();
      }}
      onDoubleClick={(e) => e.stopPropagation()}
      $colorKey={colorKey}
      $highlighted={highlighted}
    >
      {minified || !layoutInfo.label ? (
        <div className="circle" />
      ) : (
        <>
          <div className="circle" />
          {name !== DEFAULT_RESULT_NAME && <div className="label">{name}</div>}
          {type.displayName && type.displayName !== 'Nothing' && (
            <div className="type">{type.displayName}</div>
          )}
        </>
      )}
      {layoutInfo.collapsed.length > 0 && (
        <div className="collapsedCount">+ {layoutInfo.collapsed.length}</div>
      )}
    </OpIOContainer>
  );
};

const OpIOContainer = styled.div<{$colorKey: string; $highlighted: boolean}>`
  display: inline-flex;
  align-items: center;
  border-top-right-radius: 8px;
  border-bottom-right-radius: 8px;
  background: ${(p) => (p.$highlighted ? Colors.backgroundDefault() : Colors.backgroundDefault())};
  font-size: 12px;

  &:first-child {
    border-top-left-radius: 8px;
  }
  &:last-child {
    border-bottom-left-radius: 8px;
  }

  .circle {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: ${(p) => (p.$highlighted ? Colors.accentBlue() : Colors.accentGray())};
    display: inline-block;
    margin: 6px;
  }
  .label {
    line-height: 26px;
    font-family: ${FontFamily.monospace};
    font-weight: 500;
    height: 26px;
    padding-left: 2px;
    padding-right: 6px;
  }
  .type {
    padding: 1px 6px;
    background: ${Colors.backgroundBlue()};
    margin-right: 4px;
    color: ${Colors.textBlue()};
    font-family: ${FontFamily.monospace};
    font-weight: 700;
    border-radius: 4px;
  }
  .collapsedCount {
    color: ${(p) => (p.$highlighted ? Colors.textBlue() : Colors.textLight())};
    font-weight: 600;
    margin-left: -3px;
    padding-right: 4px;
  }
`;

export function metadataForCompositeParentIO(
  parentDefinition: OpNodeDefinitionFragment,
  item: OpNodeInputDefinitionFragment | OpNodeOutputDefinitionFragment,
): OpIORenderMetadata {
  const edges: Edge[] = [];
  let title = `${item.name}: ${item.type.displayName}`;

  if (parentDefinition.__typename !== 'CompositeSolidDefinition') {
    throw new Error('Parent solid is not a composite - how did this happen?');
  }

  if (item.__typename === 'InputDefinition') {
    const others = parentDefinition.inputMappings
      .filter((i) => i.definition.name === item.name)
      .map((i) => i.mappedInput);

    title += `\n\nConnected to: ${others.map(titleOfIO).join('\n')}`;
    edges.push(
      ...others.map((i) => ({
        a: `${i.solid.name}:${i.definition.name}`,
        b: PARENT_IN,
      })),
    );
  }
  if (item.__typename === 'OutputDefinition') {
    const others = parentDefinition.outputMappings
      .filter((i) => i.definition.name === item.name)
      .map((i) => i.mappedOutput);

    title += `\n\nConnected to: ${others.map(titleOfIO).join('\n')}`;
    edges.push(
      ...others.map((i) => ({
        a: `${i.solid.name}:${i.definition.name}`,
        b: PARENT_OUT,
      })),
    );
  }

  return {
    edges,
    title,
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    jumpTargetOp: edges.length === 1 ? edges[0]!.a : null,
  };
}

export function metadataForIO(
  item: OpNodeInputDefinitionFragment | OpNodeOutputDefinitionFragment,
  invocation?: OpNodeInvocationFragment,
): OpIORenderMetadata {
  const edges: Edge[] = [];

  let title = `${item.name}: ${item.type.displayName}`;
  let jumpTargetOp: string | null = null;

  if (invocation && item.__typename === 'InputDefinition') {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const others = invocation.inputs.find((i) => i.definition.name === item.name)!.dependsOn;
    if (others.length) {
      title += `\n\nFrom:\n` + others.map(titleOfIO).join('\n');
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      jumpTargetOp = others.length === 1 ? others[0]!.solid.name : null;
      edges.push(...others.map((o) => ({a: o.solid.name, b: invocation.name})));
    }
    edges.push({a: `${invocation.name}:${item.name}`, b: PARENT_IN});
  }
  if (invocation && item.__typename === 'OutputDefinition') {
    const output = invocation.outputs.find((i) => i.definition.name === item.name);
    if (!output) {
      throw new Error(
        `Invocation ${invocation.name} has no output with a definition named "${item.name}"`,
      );
    }

    const others = output.dependedBy;
    if (others.length) {
      title += '\n\nUsed By:\n' + others.map((o) => titleOfIO(o)).join('\n');
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      jumpTargetOp = others.length === 1 ? others[0]!.solid.name : null;
      edges.push(...others.map((o) => ({a: o.solid.name, b: invocation.name})));
    }
    edges.push({a: `${invocation.name}:${item.name}`, b: PARENT_OUT});
  }

  return {edges, title, jumpTargetOp};
}
