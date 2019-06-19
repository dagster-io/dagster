import * as React from "react";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { IFullPipelineLayout } from "./getFullSolidLayout";
import { PipelineGraphSolidFragment } from "./types/PipelineGraphSolidFragment";
import { SVGLabeledRect } from "./SVGComponents";
import { Edge } from "./highlighting";
import { ExternalConnectionNode } from "./ExternalConnectionNode";
import { MappingLine } from "./MappingLine";
import { titleOfIO } from "../Util";
import { SolidNameOrPath } from "../PipelineExplorer";
import {
  SolidIOBox,
  metadataForCompositeParentIO,
  PARENT_OUT,
  PARENT_IN
} from "./SolidIOBox";

interface ParentSolidNodeProps {
  layout: IFullPipelineLayout;
  solid: PipelineGraphSolidFragment;
  minified: boolean;

  highlightedEdges: Edge[];
  onDoubleClick: (solidName: string) => void;
  onClickSolid: (arg: SolidNameOrPath) => void;
  onHighlightEdges: (edges: Edge[]) => void;
}

export const ParentSolidNode: React.FunctionComponent<
  ParentSolidNodeProps
> = props => {
  const { layout, solid, minified } = props;

  const def = props.solid.definition;
  if (def.__typename !== "CompositeSolidDefinition") {
    throw new Error("Parent solid is not a composite - how did this happen?");
  }

  const parentLayout = layout.parent;
  if (!parentLayout) {
    throw new Error("Parent solid rendered when no parent layout is present.");
  }

  const { boundingBox, mappingLeftEdge, mappingLeftSpacing } = parentLayout;
  const highlightingProps = {
    highlightedEdges: props.highlightedEdges,
    onHighlightEdges: props.onHighlightEdges,
    onDoubleClick: props.onDoubleClick,
    onClickSolid: props.onClickSolid
  };

  return (
    <g>
      <SVGLabeledParentRect
        {...boundingBox}
        label={solid.definition.name}
        fill={Colors.LIGHT_GRAY5}
        minified={minified}
      />
      {def.inputMappings.map(({ definition, mappedInput }, idx) => {
        const destination = layout.solids[mappedInput.solid.name]!;
        const sourcePort = parentLayout.inputs[definition.name].port;
        const trgtPort = destination.inputs[mappedInput.definition.name].port;

        return (
          <MappingLine
            {...highlightingProps}
            key={`in-${idx}`}
            target={trgtPort}
            source={sourcePort}
            minified={minified}
            leftEdgeX={mappingLeftEdge - idx * mappingLeftSpacing}
            edge={{ a: titleOfIO(mappedInput), b: PARENT_IN }}
          />
        );
      })}
      {def.outputMappings.map(({ definition, mappedOutput }, idx) => {
        const destination = layout.solids[mappedOutput.solid.name]!;
        const sourcePort = parentLayout.outputs[definition.name].port;
        const trgtPort = destination.outputs[mappedOutput.definition.name].port;

        return (
          <MappingLine
            {...highlightingProps}
            key={`out-${idx}`}
            target={trgtPort}
            source={sourcePort}
            minified={minified}
            leftEdgeX={mappingLeftEdge - idx * mappingLeftSpacing}
            edge={{ a: titleOfIO(mappedOutput), b: PARENT_OUT }}
          />
        );
      })}
      {solid.inputs.map((input, idx) => {
        const metadata = metadataForCompositeParentIO(solid, input);
        return (
          <React.Fragment key={idx}>
            {input.dependsOn.map((dependsOn, iidx) => (
              <ExternalConnectionNode
                {...highlightingProps}
                {...metadata}
                key={iidx}
                labelAttachment="top"
                label={titleOfIO(dependsOn)}
                minified={minified}
                layout={parentLayout.dependsOn[titleOfIO(dependsOn)]}
                target={parentLayout.inputs[input.definition.name].port}
                onDoubleClickLabel={() =>
                  props.onClickSolid({ path: ["..", dependsOn.solid.name] })
                }
              />
            ))}
            <SolidIOBox
              {...highlightingProps}
              {...metadata}
              minified={minified}
              colorKey="input"
              item={input}
              layout={parentLayout.inputs[input.definition.name].layout}
            />
          </React.Fragment>
        );
      })}
      {solid.outputs.map((output, idx) => {
        const metadata = metadataForCompositeParentIO(solid, output);
        return (
          <React.Fragment key={idx}>
            {output.dependedBy.map((dependedBy, iidx) => (
              <ExternalConnectionNode
                {...highlightingProps}
                {...metadata}
                key={iidx}
                labelAttachment="bottom"
                label={titleOfIO(dependedBy)}
                minified={minified}
                layout={parentLayout.dependedBy[titleOfIO(dependedBy)]}
                target={parentLayout.outputs[output.definition.name].port}
                onDoubleClickLabel={() =>
                  props.onClickSolid({ path: ["..", dependedBy.solid.name] })
                }
              />
            ))}
            <SolidIOBox
              {...highlightingProps}
              {...metadata}
              minified={minified}
              colorKey="output"
              item={output}
              layout={parentLayout.outputs[output.definition.name].layout}
            />
          </React.Fragment>
        );
      })}
    </g>
  );
};

export const SVGLabeledParentRect = styled(SVGLabeledRect)`
  transition: x 250ms ease-out, y 250ms ease-out, width 250ms ease-out,
    height 250ms ease-out;
`;
