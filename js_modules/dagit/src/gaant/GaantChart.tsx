import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components/macro";
import {
  Slider,
  ButtonGroup,
  Button,
  Colors,
  Checkbox
} from "@blueprintjs/core";

import { weakmapMemoize } from "../Util";
import { IRunMetadataDict, EMPTY_RUN_METADATA } from "../RunMetadataProvider";
import { GaantChartExecutionPlanFragment } from "./types/GaantChartExecutionPlanFragment";
import { GaantChartTimescale } from "./GaantChartTimescale";
import { RunFragment } from "../runs/types/RunFragment";
import { GraphQueryInput } from "../GraphQueryInput";
import { filterByQuery } from "../GraphQueryImpl";
import {
  buildLayout,
  boxStyleFor,
  interestingQueriesFor
} from "./GaantChartLayout";
import {
  GaantChartLayoutOptions,
  GaantChartLayout,
  GaantChartMode,
  GaantChartBox,
  IGaantNode,
  DEFAULT_OPTIONS,
  MIN_SCALE,
  MAX_SCALE,
  BOX_HEIGHT,
  BOX_MARGIN_Y,
  LINE_SIZE,
  CSS_DURATION
} from "./Constants";

export { GaantChartMode } from "./Constants";

/**
 * Converts a Run execution plan into a tree of `GraphQueryItem` items that
 * can be used as the input to the "solid query" filtering algorithm. The idea
 * is that this data structure is generic, but it's really a fake solid tree.
 */
const toGraphQueryItems = weakmapMemoize(
  (plan: GaantChartExecutionPlanFragment) => {
    const nodeTable: { [key: string]: IGaantNode } = {};

    for (const step of plan.steps) {
      const node: IGaantNode = {
        name: step.key,
        inputs: [],
        outputs: []
      };
      nodeTable[step.key] = node;
    }

    for (const step of plan.steps) {
      for (const input of step.inputs) {
        nodeTable[step.key].inputs.push({
          dependsOn: input.dependsOn.map(d => ({
            solid: {
              name: d.key
            }
          }))
        });

        for (const upstream of input.dependsOn) {
          let output = nodeTable[upstream.key].outputs[0];
          if (!output) {
            output = {
              dependedBy: []
            };
            nodeTable[upstream.key].outputs.push(output);
          }
          output.dependedBy.push({
            solid: { name: step.key }
          });
        }
      }
    }

    return Object.values(nodeTable);
  }
);

interface GaantChartProps {
  options?: Partial<GaantChartLayoutOptions>;
  plan: GaantChartExecutionPlanFragment;
  metadata?: IRunMetadataDict;
  toolbarActions?: React.ReactChild;
  toolbarLeftActions?: React.ReactChild;
  run?: RunFragment;

  onApplyStepFilter?: (step: string) => void;
}

interface GaantChartState {
  options: GaantChartLayoutOptions;
  query: string;
}

export class GaantChart extends React.Component<
  GaantChartProps,
  GaantChartState
> {
  static fragments = {
    GaantChartExecutionPlanFragment: gql`
      fragment GaantChartExecutionPlanFragment on ExecutionPlan {
        steps {
          key
          kind
        }
        steps {
          key
          inputs {
            dependsOn {
              key
              outputs {
                name
                type {
                  name
                }
              }
            }
          }
        }
        artifactsPersisted
      }
    `
  };

  constructor(props: GaantChartProps) {
    super(props);

    this.state = {
      query: "*",
      options: Object.assign(DEFAULT_OPTIONS, props.options)
    };
  }

  updateOptions = (changes: Partial<GaantChartLayoutOptions>) => {
    this.setState({
      ...this.state,
      options: { ...this.state.options, ...changes }
    });
  };

  onWheel = (event: React.WheelEvent) => {
    const next = this.state.options.scale * (1 - event.deltaY * 0.0025);
    this.updateOptions({
      scale: Math.max(MIN_SCALE, Math.min(MAX_SCALE, next))
    });
  };

  render() {
    const { metadata = EMPTY_RUN_METADATA, plan } = this.props;
    const { query, options } = this.state;

    const graph = toGraphQueryItems(plan);
    const graphFiltered = filterByQuery(graph, query);
    const layout = buildLayout({
      nodes: graphFiltered.all,
      metadata,
      options
    });

    // todo perf: We can break buildLayout into a function that does not need metadata
    // and then a post-processor that resizes/shifts things using `metadata`. Then we can
    // memoize the time consuming vertical layout work.
    return (
      <GaantChartContainer onWheel={this.onWheel}>
        <OptionsContainer>
          {this.props.toolbarLeftActions}
          {this.props.toolbarLeftActions && <OptionsDivider />}
          <ButtonGroup style={{ flexShrink: 0 }}>
            <Button
              key={GaantChartMode.FLAT}
              small={true}
              icon="column-layout"
              title={"Flat"}
              active={options.mode === GaantChartMode.FLAT}
              onClick={() => this.updateOptions({ mode: GaantChartMode.FLAT })}
            />
            <Button
              key={GaantChartMode.WATERFALL}
              small={true}
              icon="gantt-chart"
              title={"Waterfall"}
              active={options.mode === GaantChartMode.WATERFALL}
              onClick={() =>
                this.updateOptions({ mode: GaantChartMode.WATERFALL })
              }
            />
            {!options.hideTimedMode && (
              <Button
                key={GaantChartMode.WATERFALL_TIMED}
                small={true}
                icon="time"
                rightIcon="gantt-chart"
                title={"Waterfall with Execution Timing"}
                active={options.mode === GaantChartMode.WATERFALL_TIMED}
                onClick={() =>
                  this.updateOptions({ mode: GaantChartMode.WATERFALL_TIMED })
                }
              />
            )}
          </ButtonGroup>
          {options.mode === GaantChartMode.WATERFALL_TIMED && (
            <>
              <div style={{ width: 15 }} />
              <Checkbox
                style={{ marginBottom: 0 }}
                label="Hide waiting"
                checked={options.hideWaiting}
                onClick={() =>
                  this.updateOptions({ hideWaiting: !options.hideWaiting })
                }
              />
              <div style={{ width: 15 }} />
              <div style={{ width: 200 }}>
                <Slider
                  min={MIN_SCALE}
                  max={MAX_SCALE}
                  stepSize={0.01}
                  labelRenderer={false}
                  value={options.scale}
                  onChange={v => this.updateOptions({ scale: v })}
                />
              </div>
            </>
          )}
          <div style={{ flex: 1 }} />
          {this.props.toolbarActions}
        </OptionsContainer>
        <GaantChartContent {...this.props} {...this.state} layout={layout} />
        <GraphQueryInput
          items={graph}
          value={query}
          onChange={q => this.setState({ query: q })}
          presets={interestingQueriesFor(metadata, layout)}
        />
      </GaantChartContainer>
    );
  }
}

const GaantChartContent = (
  props: GaantChartProps & GaantChartState & { layout: GaantChartLayout }
) => {
  const [scrollLeft, setScrollLeft] = React.useState<number>(0);
  const [hoveredIdx, setHoveredIdx] = React.useState<number>(-1);
  const { options, layout, metadata = EMPTY_RUN_METADATA } = props;

  const items: React.ReactChild[] = [];
  const hovered = layout.boxes[hoveredIdx];

  layout.boxes.forEach((box, idx) => {
    const highlighted = hovered === box || hovered?.children.includes(box);
    const style = boxStyleFor(box.node, { metadata, options });

    items.push(
      <div
        key={box.node.name}
        style={{
          left: box.x,
          top: BOX_HEIGHT * box.y + BOX_MARGIN_Y,
          width: box.width,
          ...style
        }}
        className={`box ${highlighted && "highlighted"}`}
        onClick={() => props.onApplyStepFilter?.(box.node.name)}
        onMouseEnter={() => setHoveredIdx(idx)}
        onMouseLeave={() => setHoveredIdx(-1)}
      >
        {box.node.name}
      </div>
    );
    if (options.mode !== GaantChartMode.FLAT) {
      box.children.forEach((child, childIdx) => {
        const childIsRendered = layout.boxes.includes(child);
        items.push(
          <GaantLine
            highlighted={hovered && (hovered === box || hovered === child)}
            dotted={!childIsRendered}
            key={`${box.node.name}-${child.node.name}-${childIdx}`}
            start={box}
            end={child}
            depIdx={childIdx}
          />
        );
      });
    }
  });

  return (
    <>
      {options.mode === GaantChartMode.WATERFALL_TIMED && (
        <GaantChartTimescale
          scale={options.scale}
          scrollLeft={scrollLeft}
          startMs={metadata.minStepStart || 0}
          nowMs={metadata.mostRecentLogAt}
          highlightedMs={
            hovered
              ? ([
                  metadata.steps[hovered.node.name]?.start,
                  metadata.steps[hovered.node.name]?.finish
                ].filter(Number) as number[])
              : []
          }
        />
      )}
      <div
        style={{ overflow: "scroll", flex: 1 }}
        onScroll={e => setScrollLeft(e.currentTarget.scrollLeft)}
      >
        <div style={{ position: "relative" }}>{items}</div>
      </div>
    </>
  );
};

const GaantLine = React.memo(
  ({
    start,
    end,
    dotted,
    highlighted,
    depIdx
  }: {
    start: GaantChartBox;
    end: GaantChartBox;
    dotted: boolean;
    highlighted: boolean;
    depIdx: number;
  }) => {
    const startIdx = start.y;
    const endIdx = end.y;

    const minIdx = Math.min(startIdx, endIdx);
    const maxIdx = Math.max(startIdx, endIdx);

    const maxY = maxIdx * BOX_HEIGHT + BOX_MARGIN_Y;
    const minY = minIdx * BOX_HEIGHT + BOX_HEIGHT / 2;

    const minX = Math.min(start.x + start.width, end.x + end.width);
    const maxX =
      maxIdx === minIdx
        ? Math.max(start.x, end.x)
        : Math.max(start.x + start.width / 2, end.x + end.width / 2);

    const border = `${LINE_SIZE}px ${dotted ? "dotted" : "solid"} ${
      highlighted ? Colors.DARK_GRAY1 : Colors.LIGHT_GRAY3
    }`;

    return (
      <>
        <div
          className="line"
          data-info={`from ${start.node.name} to ${end.node.name}`}
          style={{
            height: 1,
            left: minX,
            width: dotted ? 50 : maxX + (depIdx % 10) * LINE_SIZE - minX,
            top: minY - 1,
            borderTop: border,
            zIndex: highlighted ? 100 : 1
          }}
        />
        {maxIdx !== minIdx && !dotted && (
          <div
            className="line"
            data-info={`from ${start.node.name} to ${end.node.name}`}
            style={{
              width: 1,
              left: maxX + (depIdx % 10) * LINE_SIZE,
              top: minY,
              height: maxY - minY,
              borderRight: border,
              zIndex: highlighted ? 100 : 1
            }}
          />
        )}
      </>
    );
  }
);

// Note: It is much faster to use standard CSS class selectors here than make
// each box and line a styled-component because all styled components register
// listeners for the "theme" React context.
const GaantChartContainer = styled.div`
  height: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  z-index: 2;
  user-select: none;
  background: ${Colors.WHITE};

  .line {
    position: absolute;
    user-select: none;
    pointer-events: none;
    transition: top ${CSS_DURATION} linear, left ${CSS_DURATION} linear,
      width ${CSS_DURATION} linear, height ${CSS_DURATION} linear;
  }

  .box {
    display: inline-block;
    position: absolute;
    height: ${BOX_HEIGHT - BOX_MARGIN_Y * 2}px;
    color: white;
    padding: 2px;
    font-size: 11px;
    border: 1px solid transparent;
    overflow: hidden;
    z-index: 2;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    border-radius: 2px;
    user-select: text;

    transition: top ${CSS_DURATION} linear, left ${CSS_DURATION} linear,
      width ${CSS_DURATION} linear, height ${CSS_DURATION} linear;

    &.highlighted {
      border: 1px solid ${Colors.DARK_GRAY1};
    }
  }
`;

const OptionsContainer = styled.div`
  height: 40px;
  display: flex;
  align-items: center;
  padding: 5px 15px;
  border-bottom: 1px solid #A7B6C2;
  box-shadow: 0 1px 3px rgba(0,0,0,0.07);
  background: ${Colors.WHITE};
  flex-shrink: 0;
  z-index: 3;
}`;

const OptionsDivider = styled.div`
  width: 1px;
  height: 25px;
  padding-left: 7px;
  margin-left: 7px;
  border-left: 1px solid ${Colors.LIGHT_GRAY3};
`;
