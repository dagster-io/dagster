import {Colors} from '@dagster-io/ui-components';
import {Fragment} from 'react';
import styled from 'styled-components';

import {ExternalConnectionNode} from './ExternalConnectionNode';
import {MappingLine} from './MappingLine';
import {OpIOBox, PARENT_IN, PARENT_OUT, metadataForCompositeParentIO} from './OpIOBox';
import {SVGMonospaceText} from './SVGComponents';
import {OpGraphLayout} from './asyncGraphLayout';
import {Edge} from './common';
import {OpGraphOpFragment} from './types/OpGraph.types';
import {titleOfIO} from '../app/titleOfIO';
import {OpNameOrPath} from '../ops/OpNameOrPath';

interface ParentOpNodeProps {
  layout: OpGraphLayout;
  op: OpGraphOpFragment;
  minified: boolean;

  highlightedEdges: Edge[];
  onDoubleClick: (opName: string) => void;
  onClickOp: (arg: OpNameOrPath) => void;
  onHighlightEdges: (edges: Edge[]) => void;
}

export const ParentOpNode = (props: ParentOpNodeProps) => {
  const {layout, op, minified} = props;

  const def = props.op.definition;
  if (def.__typename !== 'CompositeSolidDefinition') {
    throw new Error('Parent op is not a composite - how did this happen?');
  }

  const parentLayout = layout.parent;
  if (!parentLayout) {
    throw new Error('Parent op rendered when no parent layout is present.');
  }

  const {bounds, mappingLeftEdge, mappingLeftSpacing} = parentLayout;
  const highlightingProps = {
    highlightedEdges: props.highlightedEdges,
    onHighlightEdges: props.onHighlightEdges,
    onDoubleClick: props.onDoubleClick,
    onClickOp: props.onClickOp,
  };

  if (bounds.height < 0 || bounds.width < 0) {
    return <g />;
  }
  return (
    <>
      <SVGLabeledParentRect
        {...bounds}
        label={op.definition.name}
        fill={Colors.backgroundYellow()}
        minified={minified}
      />
      {def.inputMappings.map(({definition, mappedInput}, idx) => {
        // The mappings link the IOs of the parent graph op to the
        // input / outputs of ops within the subgraph.

        const parentIO = parentLayout.inputs[definition.name];
        const destinationNode = layout.nodes[mappedInput.solid.name];
        if (!destinationNode || !parentIO) {
          console.warn(
            `Assertion failure - Unable to find ${mappedInput.solid.name} in the layout ` +
              `or ${definition.name} in the parent layout`,
          );
          return <g key={mappedInput.solid.name} />;
        }

        const destinationIOFull = destinationNode.inputs[mappedInput.definition.name];
        const destinationIOCollapsed = Object.values(destinationNode.inputs).find((o) =>
          o.collapsed.includes(mappedInput.definition.name),
        );
        const destinationIO = destinationIOFull || destinationIOCollapsed;
        if (!destinationIO) {
          console.warn(
            `Assertion failure - Unable to find port for ${mappedInput.definition.name}`,
          );
          return <g key={mappedInput.solid.name} />;
        }

        return (
          <MappingLine
            {...highlightingProps}
            key={`in-${idx}`}
            target={destinationIO.port}
            source={parentIO.port}
            minified={minified}
            leftEdgeX={mappingLeftEdge - idx * mappingLeftSpacing}
            edge={{a: titleOfIO(mappedInput), b: PARENT_IN}}
          />
        );
      })}
      {def.outputMappings.map(({definition, mappedOutput}, idx) => {
        const parentIO = parentLayout.outputs[definition.name];
        const destination = layout.nodes[mappedOutput.solid.name];
        if (!destination || !parentIO) {
          console.warn(
            `Unable to find ${mappedOutput.solid.name} in the layout ` +
              `or ${definition.name} in the parent layout`,
          );
          return <g key={mappedOutput.solid.name} />;
        }

        const destinationIOFull = destination.outputs[mappedOutput.definition.name];
        const destinationIOCollapsed = Object.values(destination.outputs).find((o) =>
          o.collapsed.includes(mappedOutput.definition.name),
        );
        const destinationIO = destinationIOFull || destinationIOCollapsed;
        if (!destinationIO) {
          console.warn(`Unable to find port for ${mappedOutput.definition.name}`);
          return <g key={mappedOutput.solid.name} />;
        }

        return (
          <MappingLine
            {...highlightingProps}
            key={`out-${idx}`}
            target={destinationIO.port}
            source={parentIO.port}
            minified={minified}
            leftEdgeX={mappingLeftEdge - idx * mappingLeftSpacing}
            edge={{a: titleOfIO(mappedOutput), b: PARENT_OUT}}
          />
        );
      })}
      {op.definition.inputDefinitions.map((input, idx) => {
        const metadata = metadataForCompositeParentIO(op.definition, input);
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        const invocationInput = op.inputs.find((i) => i.definition.name === input.name)!;
        return (
          <Fragment key={idx}>
            {invocationInput.dependsOn.map((dependsOn, iidx) => (
              <ExternalConnectionNode
                {...highlightingProps}
                {...metadata}
                key={iidx}
                labelAttachment="top"
                label={titleOfIO(dependsOn)}
                minified={minified}
                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                layout={parentLayout.dependsOn[titleOfIO(dependsOn)]!}
                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                target={parentLayout.inputs[input.name]!.port}
                onDoubleClickLabel={() => props.onClickOp({path: ['..', dependsOn.solid.name]})}
              />
            ))}
          </Fragment>
        );
      })}
      {op.definition.outputDefinitions.map((output, idx) => {
        const metadata = metadataForCompositeParentIO(op.definition, output);
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        const invocationOutput = op.outputs.find((i) => i.definition.name === output.name)!;
        return (
          <Fragment key={idx}>
            {invocationOutput.dependedBy.map((dependedBy, iidx) => (
              <ExternalConnectionNode
                {...highlightingProps}
                {...metadata}
                key={iidx}
                labelAttachment="bottom"
                label={titleOfIO(dependedBy)}
                minified={minified}
                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                layout={parentLayout.dependedBy[titleOfIO(dependedBy)]!}
                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                target={parentLayout.outputs[output.name]!.port}
                onDoubleClickLabel={() => props.onClickOp({path: ['..', dependedBy.solid.name]})}
              />
            ))}
          </Fragment>
        );
      })}
      <foreignObject width={layout.width} height={layout.height} style={{pointerEvents: 'none'}}>
        {op.definition.inputDefinitions.map((input, idx) => (
          <OpIOBox
            {...highlightingProps}
            {...metadataForCompositeParentIO(op.definition, input)}
            key={idx}
            minified={minified}
            colorKey="input"
            item={input}
            layoutInfo={parentLayout.inputs[input.name]}
          />
        ))}
        {op.definition.outputDefinitions.map((output, idx) => (
          <OpIOBox
            {...highlightingProps}
            {...metadataForCompositeParentIO(op.definition, output)}
            key={idx}
            minified={minified}
            colorKey="output"
            item={output}
            layoutInfo={parentLayout.outputs[output.name]}
          />
        ))}
      </foreignObject>
    </>
  );
};

const SVGLabeledRect = ({
  minified,
  label,
  fill,
  className,
  ...rect
}: {
  x: number;
  y: number;
  minified: boolean;
  width: number;
  height: number;
  label: string;
  fill: string;
  className?: string;
}) => (
  <g>
    <rect
      {...rect}
      fill={fill}
      stroke={Colors.keylineDefault()}
      strokeWidth={1}
      className={className}
    />
    <SVGMonospaceText
      x={rect.x + (minified ? 10 : 5)}
      y={rect.y + (minified ? 10 : 5)}
      height={undefined}
      size={minified ? 30 : 16}
      text={label}
      fill="#979797"
    />
  </g>
);

export const SVGLabeledParentRect = styled(SVGLabeledRect)`
  transition:
    x 250ms ease-out,
    y 250ms ease-out,
    width 250ms ease-out,
    height 250ms ease-out;
`;
