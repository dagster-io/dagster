import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {titleOfIO} from 'src/Util';
import {ExternalConnectionNode} from 'src/graph/ExternalConnectionNode';
import {MappingLine} from 'src/graph/MappingLine';
import {SVGLabeledRect} from 'src/graph/SVGComponents';
import {
  PARENT_IN,
  PARENT_OUT,
  SolidIOBox,
  metadataForCompositeParentIO,
} from 'src/graph/SolidIOBox';
import {IFullPipelineLayout} from 'src/graph/getFullSolidLayout';
import {Edge} from 'src/graph/highlighting';
import {PipelineGraphSolidFragment} from 'src/graph/types/PipelineGraphSolidFragment';
import {SolidNameOrPath} from 'src/solids/SolidNameOrPath';

interface ParentSolidNodeProps {
  layout: IFullPipelineLayout;
  solid: PipelineGraphSolidFragment;
  minified: boolean;

  highlightedEdges: Edge[];
  onDoubleClick: (solidName: string) => void;
  onClickSolid: (arg: SolidNameOrPath) => void;
  onHighlightEdges: (edges: Edge[]) => void;
}

export const ParentSolidNode: React.FunctionComponent<ParentSolidNodeProps> = (props) => {
  const {layout, solid, minified} = props;

  const def = props.solid.definition;
  if (def.__typename !== 'CompositeSolidDefinition') {
    throw new Error('Parent solid is not a composite - how did this happen?');
  }

  const parentLayout = layout.parent;
  if (!parentLayout) {
    throw new Error('Parent solid rendered when no parent layout is present.');
  }

  const {boundingBox, mappingLeftEdge, mappingLeftSpacing} = parentLayout;
  const highlightingProps = {
    highlightedEdges: props.highlightedEdges,
    onHighlightEdges: props.onHighlightEdges,
    onDoubleClick: props.onDoubleClick,
    onClickSolid: props.onClickSolid,
  };

  if (boundingBox.height < 0 || boundingBox.width < 0) {
    return <g />;
  }
  return (
    <>
      <SVGLabeledParentRect
        {...boundingBox}
        label={solid.definition.name}
        fill={Colors.LIGHT_GRAY5}
        minified={minified}
      />
      {def.inputMappings.map(({definition, mappedInput}, idx) => {
        const destination = layout.solids[mappedInput.solid.name];
        if (!destination) {
          return <g />;
        }
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
            edge={{a: titleOfIO(mappedInput), b: PARENT_IN}}
          />
        );
      })}
      {def.outputMappings.map(({definition, mappedOutput}, idx) => {
        const destination = layout.solids[mappedOutput.solid.name];
        if (!destination) {
          return <g />;
        }
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
            edge={{a: titleOfIO(mappedOutput), b: PARENT_OUT}}
          />
        );
      })}
      {solid.definition.inputDefinitions.map((input, idx) => {
        const metadata = metadataForCompositeParentIO(solid.definition, input);
        const invocationInput = solid.inputs.find((i) => i.definition.name === input.name)!;

        return (
          <React.Fragment key={idx}>
            {invocationInput.dependsOn.map((dependsOn, iidx) => (
              <ExternalConnectionNode
                {...highlightingProps}
                {...metadata}
                key={iidx}
                labelAttachment="top"
                label={titleOfIO(dependsOn)}
                minified={minified}
                layout={parentLayout.dependsOn[titleOfIO(dependsOn)]}
                target={parentLayout.inputs[input.name].port}
                onDoubleClickLabel={() => props.onClickSolid({path: ['..', dependsOn.solid.name]})}
              />
            ))}
            <SolidIOBox
              {...highlightingProps}
              {...metadata}
              minified={minified}
              colorKey="input"
              item={input}
              layout={parentLayout.inputs[input.name].layout}
            />
          </React.Fragment>
        );
      })}
      {solid.definition.outputDefinitions.map((output, idx) => {
        const metadata = metadataForCompositeParentIO(solid.definition, output);
        const invocationOutput = solid.outputs.find((i) => i.definition.name === output.name)!;

        return (
          <React.Fragment key={idx}>
            {invocationOutput.dependedBy.map((dependedBy, iidx) => (
              <ExternalConnectionNode
                {...highlightingProps}
                {...metadata}
                key={iidx}
                labelAttachment="bottom"
                label={titleOfIO(dependedBy)}
                minified={minified}
                layout={parentLayout.dependedBy[titleOfIO(dependedBy)]}
                target={parentLayout.outputs[output.name].port}
                onDoubleClickLabel={() => props.onClickSolid({path: ['..', dependedBy.solid.name]})}
              />
            ))}
            <SolidIOBox
              {...highlightingProps}
              {...metadata}
              minified={minified}
              colorKey="output"
              item={output}
              layout={parentLayout.outputs[output.name].layout}
            />
          </React.Fragment>
        );
      })}
    </>
  );
};

export const SVGLabeledParentRect = styled(SVGLabeledRect)`
  transition: x 250ms ease-out, y 250ms ease-out, width 250ms ease-out, height 250ms ease-out;
`;
