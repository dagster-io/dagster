import * as React from "react";
import PipelineColorScale from "./PipelineColorScale";
import { ILayout } from "./getFullSolidLayout";
import {
  SolidNodeFragment,
  SolidNodeFragment_inputs,
  SolidNodeFragment_outputs
} from "./types/SolidNodeFragment";
import {
  SVGEllipseInRect,
  SVGFlowLayoutRect,
  SVGMonospaceText
} from "./SVGComponents";

import { DEFAULT_RESULT_NAME, titleOfIO } from "../Util";
import { Edge, isHighlighted } from "./highlighting";

export const PARENT_IN = "PARENT_IN";
export const PARENT_OUT = "PARENT_OUT";

interface SolidIORenderMetadata {
  edges: Edge[];
  jumpTargetSolid: string | null;
  title: string;
}

interface SolidIOBoxProps extends SolidIORenderMetadata {
  colorKey: "input" | "output";
  item: SolidNodeFragment_inputs | SolidNodeFragment_outputs;
  layout: ILayout;

  // Passed through from Solid props
  minified: boolean;
  highlightedEdges: Edge[];
  onDoubleClick: (solidName: string) => void;
  onHighlightEdges: (edges: Edge[]) => void;
}

export const SolidIOBox: React.FunctionComponent<SolidIOBoxProps> = ({
  minified,
  title,
  jumpTargetSolid,
  edges,
  highlightedEdges,
  layout,
  colorKey,
  item,
  onDoubleClick,
  onHighlightEdges
}) => {
  const { x, y, width, height } = layout;
  const { name, type } = item.definition;
  const showText = width === 0 && !minified;
  const highlighted = edges.some(e => isHighlighted(highlightedEdges, e));

  return (
    <g
      onMouseEnter={() => onHighlightEdges(edges)}
      onMouseLeave={() => onHighlightEdges([])}
      onClick={e => {
        jumpTargetSolid && onDoubleClick(jumpTargetSolid);
        e.stopPropagation();
      }}
      onDoubleClick={e => e.stopPropagation()}
    >
      <title>{title}</title>
      <SVGFlowLayoutRect
        x={x}
        y={y}
        stroke="#979797"
        strokeWidth={1}
        maxWidth={300}
        fill={
          highlighted
            ? PipelineColorScale(`${colorKey}Highlighted`)
            : PipelineColorScale(colorKey)
        }
        padding={8}
        spacing={7}
        height={height}
      >
        <SVGEllipseInRect
          width={14}
          height={14}
          fill="rgba(0, 0, 0, 0.3)"
          stroke="white"
          strokeWidth={1.5}
        />
        {showText && name !== DEFAULT_RESULT_NAME && (
          <SVGMonospaceText text={`${name}:`} fill="#FFF" size={14} />
        )}
        {showText && type.displayName && (
          <SVGFlowLayoutRect
            rx={4}
            ry={4}
            fill="#d6ecff"
            stroke="#2491eb"
            strokeWidth={1}
            height={27}
            spacing={0}
            padding={4}
          >
            <SVGMonospaceText text={type.displayName} size={14} fill="#222" />
          </SVGFlowLayoutRect>
        )}
      </SVGFlowLayoutRect>
    </g>
  );
};

export function metadataForCompositeParentIO(
  solid: SolidNodeFragment,
  item: SolidNodeFragment_inputs | SolidNodeFragment_outputs
): SolidIORenderMetadata {
  const edges: Edge[] = [];
  let title = `${item.definition.name}: ${item.definition.type.displayName}`;

  if (solid.definition.__typename !== "CompositeSolidDefinition") {
    throw new Error("Parent solid is not a composite - how did this happen?");
  }

  if (item.__typename === "Input") {
    const others = solid.definition.inputMappings
      .filter(i => i.definition.name === item.definition.name)
      .map(i => i.mappedInput);

    title += `\n\nConnected to: ${others.map(titleOfIO).join("\n")}`;
    edges.push(
      ...others.map(i => ({
        a: `${i.solid.name}:${i.definition.name}`,
        b: PARENT_IN
      }))
    );
  }
  if (item.__typename === "Output") {
    const others = solid.definition.outputMappings
      .filter(i => i.definition.name === item.definition.name)
      .map(i => i.mappedOutput);

    title += `\n\nConnected to: ${others.map(titleOfIO).join("\n")}`;
    edges.push(
      ...others.map(i => ({
        a: `${i.solid.name}:${i.definition.name}`,
        b: PARENT_OUT
      }))
    );
  }

  return {
    edges,
    title,
    jumpTargetSolid: edges.length === 1 ? edges[0].a : null
  };
}

export function metadataForIO(
  { name }: SolidNodeFragment,
  item: SolidNodeFragment_inputs | SolidNodeFragment_outputs
): SolidIORenderMetadata {
  const edges: Edge[] = [];

  let title = `${item.definition.name}: ${item.definition.type.displayName}`;
  let jumpTargetSolid: string | null = null;

  if (item.__typename === "Input") {
    const others = item.dependsOn;
    if (others.length) {
      title += `\n\nFrom:\n` + others.map(titleOfIO).join("\n");
      jumpTargetSolid = others.length === 1 ? others[0].solid.name : null;
      edges.push(...others.map(o => ({ a: o.solid.name, b: name })));
    }
    edges.push({ a: `${name}:${item.definition.name}`, b: PARENT_IN });
  }
  if (item.__typename === "Output") {
    const others = item.dependedBy;
    if (others.length) {
      title += "\n\nUsed By:\n" + others.map(o => titleOfIO(o)).join("\n");
      jumpTargetSolid = others.length === 1 ? others[0].solid.name : null;
      edges.push(...others.map(o => ({ a: o.solid.name, b: name })));
    }
    edges.push({ a: `${name}:${item.definition.name}`, b: PARENT_OUT });
  }

  return { edges, title, jumpTargetSolid };
}
