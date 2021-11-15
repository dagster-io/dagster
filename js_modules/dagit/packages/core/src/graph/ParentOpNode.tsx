import * as React from 'react';
import styled from 'styled-components/macro';

import {titleOfIO} from '../app/titleOfIO';
import {OpNameOrPath} from '../ops/OpNameOrPath';
import {ColorsWIP} from '../ui/Colors';

import {ExternalConnectionNode} from './ExternalConnectionNode';
import {MappingLine} from './MappingLine';
import {metadataForCompositeParentIO, PARENT_IN, PARENT_OUT, OpIOBox} from './OpIOBox';
import {position} from './OpNode';
import {SVGLabeledRect} from './SVGComponents';
import {IFullPipelineLayout} from './getFullSolidLayout';
import {Edge} from './highlighting';
import {PipelineGraphSolidFragment} from './types/PipelineGraphSolidFragment';

interface ParentOpNodeProps {
  layout: IFullPipelineLayout;
  solid: PipelineGraphSolidFragment;
  minified: boolean;

  highlightedEdges: Edge[];
  onDoubleClick: (solidName: string) => void;
  onClickOp: (arg: OpNameOrPath) => void;
  onHighlightEdges: (edges: Edge[]) => void;
}

export const ParentOpNode: React.FunctionComponent<ParentOpNodeProps> = (props) => {
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
    onClickOp: props.onClickOp,
  };

  if (boundingBox.height < 0 || boundingBox.width < 0) {
    return <g />;
  }
  return (
    <>
      <SVGLabeledParentRect
        {...boundingBox}
        label={solid.definition.name}
        fill={ColorsWIP.Gray50}
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
                onDoubleClickLabel={() => props.onClickOp({path: ['..', dependsOn.solid.name]})}
              />
            ))}
            <OpIOBox
              {...highlightingProps}
              {...metadata}
              minified={minified}
              colorKey="input"
              item={input}
              style={position(parentLayout.inputs[input.name].layout)}
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
                onDoubleClickLabel={() => props.onClickOp({path: ['..', dependedBy.solid.name]})}
              />
            ))}
            <OpIOBox
              {...highlightingProps}
              {...metadata}
              minified={minified}
              colorKey="output"
              item={output}
              style={position(parentLayout.outputs[output.name].layout)}
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
