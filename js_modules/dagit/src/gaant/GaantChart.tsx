import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components/macro";
import { ButtonGroup, Button, Colors, Checkbox } from "@blueprintjs/core";
import { isEqual } from "lodash";

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
  interestingQueriesFor,
  adjustLayoutWithRunMetadata,
  BuildLayoutParams
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
  CSS_DURATION,
  BOX_DOT_WIDTH_CUTOFF,
  BOX_SHOW_LABEL_WIDTH_CUTOFF,
  BOX_DOT_SIZE
} from "./Constants";
import { SplitPanelContainer } from "../SplitPanelContainer";
import { GaantStatusPanel } from "./GaantStatusPanel";

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
  selectedStep: string | null;
  plan: GaantChartExecutionPlanFragment;
  options?: Partial<GaantChartLayoutOptions>;
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

  _cachedLayout: GaantChartLayout | null = null;
  _cachedLayoutParams: BuildLayoutParams | null = null;

  constructor(props: GaantChartProps) {
    super(props);

    this.state = {
      query: "*",
      options: Object.assign(DEFAULT_OPTIONS, props.options)
    };
  }

  getLayout = (params: BuildLayoutParams) => {
    if (
      !this._cachedLayoutParams ||
      this._cachedLayoutParams.nodes !== params.nodes ||
      this._cachedLayoutParams.mode !== params.mode
    ) {
      this._cachedLayout = buildLayout(params);
      this._cachedLayoutParams = params;
    }
    return this._cachedLayout!;
  };

  updateOptions = (changes: Partial<GaantChartLayoutOptions>) => {
    this.setState({
      ...this.state,
      options: { ...this.state.options, ...changes }
    });
  };

  render() {
    const { metadata = EMPTY_RUN_METADATA, plan, selectedStep } = this.props;
    const { query, options } = this.state;

    const graph = toGraphQueryItems(plan);
    const graphFiltered = filterByQuery(graph, query);
    const layout = adjustLayoutWithRunMetadata(
      this.getLayout({
        nodes: graphFiltered.all,
        mode: options.mode
      }),
      options,
      metadata
    );

    const content = (
      <>
        <GaantChartContent {...this.props} {...this.state} layout={layout} />
        <GraphQueryInput
          items={graph}
          value={query}
          onChange={q => this.setState({ query: q })}
          presets={interestingQueriesFor(metadata, layout)}
        />
      </>
    );
    // todo perf: We can break buildLayout into a function that does not need metadata
    // and then a post-processor that resizes/shifts things using `metadata`. Then we can
    // memoize the time consuming vertical layout work.
    return (
      <GaantChartContainer>
        <OptionsContainer>
          {this.props.toolbarLeftActions}
          {this.props.toolbarLeftActions && <OptionsDivider />}
          <GaantChartModeControl
            value={options.mode}
            onChange={mode => this.updateOptions({ mode })}
            hideTimedMode={options.hideTimedMode}
          />
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
                <LogScaleSlider
                  value={options.scale}
                  onChange={v => this.updateOptions({ scale: v })}
                />
              </div>
            </>
          )}
          <div style={{ flex: 1 }} />
          {this.props.toolbarActions}
        </OptionsContainer>

        {metadata && options.mode === GaantChartMode.WATERFALL_TIMED ? (
          <SplitPanelContainer
            identifier="gaant-split"
            axis="horizontal"
            first={content}
            firstInitialPercent={80}
            second={
              <GaantStatusPanel
                {...this.props}
                metadata={metadata}
                selectedStep={selectedStep}
                onHighlightStep={name => {
                  document.dispatchEvent(
                    new CustomEvent("highlight-node", { detail: { name } })
                  );
                }}
              />
            }
          />
        ) : (
          content
        )}
      </GaantChartContainer>
    );
  }
}

type GaantChartContentProps = GaantChartProps &
  GaantChartState & { layout: GaantChartLayout };

interface GaantViewport {
  left: number;
  top: number;
  width: number;
  height: number;
}

const useViewport = () => {
  const ref = React.useRef<any>();
  const [viewport, setViewport] = React.useState<GaantViewport>({
    left: 0,
    width: 0,
    top: 0,
    height: 0
  });

  React.useEffect(() => {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    if (rect.width !== viewport.width || rect.height !== viewport.height) {
      setViewport({ ...viewport, width: rect.width, height: rect.height });
    }
  }, [viewport, setViewport]);

  const onScroll = (e: React.UIEvent) => {
    setViewport({
      ...viewport,
      left: e.currentTarget.scrollLeft,
      top: e.currentTarget.scrollTop
    });
  };

  return {
    viewport,
    setViewport,
    containerProps: { ref, onScroll }
  };
};

const GaantChartContent: React.FunctionComponent<GaantChartContentProps> = props => {
  const { viewport, setViewport, containerProps } = useViewport();
  const [hoveredIdx, setHoveredIdx] = React.useState<number>(-1);
  const { options, layout, metadata = EMPTY_RUN_METADATA } = props;

  const items: React.ReactChild[] = [];
  const focused = layout.boxes.find(b => b.node.name === props.selectedStep);
  const hovered = layout.boxes[hoveredIdx];

  React.useEffect(() => {
    const onEvent = (e: CustomEvent) => {
      const idx = layout.boxes.findIndex(b => b.node.name === e.detail.name);
      setHoveredIdx(idx);
    };
    document.addEventListener("highlight-node", onEvent);
    return () => document.removeEventListener("highlight-node", onEvent);
  });

  const layoutSize = {
    width: Math.max(0, ...layout.boxes.map(b => b.x + b.width)),
    height: Math.max(0, ...layout.boxes.map(b => b.y * BOX_HEIGHT + BOX_HEIGHT))
  };

  const intersectsViewport = (bounds: Bounds) =>
    bounds.minX < viewport.left + viewport.width &&
    bounds.maxX > viewport.left &&
    bounds.minY < viewport.top + viewport.height &&
    bounds.maxY > viewport.top;

  if (options.mode !== GaantChartMode.FLAT) {
    layout.boxes.forEach(box => {
      box.children.forEach((child, childIdx) => {
        const bounds = boundsForLine(box, child);
        if (!intersectsViewport(bounds)) return;

        const childIsRendered = layout.boxes.includes(child);
        items.push(
          <GaantLine
            darkened={
              (focused || hovered) === box || (focused || hovered) === child
            }
            dotted={!childIsRendered}
            key={`${box.node.name}-${child.node.name}-${childIdx}`}
            depIdx={childIdx}
            {...bounds}
          />
        );
      });
    });
  }

  layout.boxes.forEach((box, idx) => {
    const bounds = boundsForBox(box);
    if (!intersectsViewport(bounds)) return;

    const useDot = box.width === BOX_DOT_WIDTH_CUTOFF;

    items.push(
      <div
        key={box.node.name}
        title={box.node.name}
        onClick={() => props.onApplyStepFilter?.(box.node.name)}
        onMouseEnter={() => setHoveredIdx(idx)}
        onMouseLeave={() => setHoveredIdx(-1)}
        className={`
            ${useDot ? "dot" : "box"}
            ${focused === box && "focused"}
            ${hovered === box && "hovered"}`}
        style={{
          left: bounds.minX,
          top:
            bounds.minY +
            (useDot ? (BOX_HEIGHT - BOX_DOT_SIZE) / 2 : BOX_MARGIN_Y),
          width: useDot ? BOX_DOT_SIZE : box.width,
          ...boxStyleFor(box.node.name, { metadata, options })
        }}
      >
        {box.width > BOX_SHOW_LABEL_WIDTH_CUTOFF ? box.node.name : undefined}
      </div>
    );
  });

  return (
    <>
      {options.mode === GaantChartMode.WATERFALL_TIMED && (
        <GaantChartTimescale
          scale={options.scale}
          scrollLeft={viewport.left}
          startMs={metadata.minStepStart || 0}
          nowMs={metadata.mostRecentLogAt}
          highlightedMs={
            focused
              ? ([
                  metadata.steps[focused.node.name]?.start,
                  metadata.steps[focused.node.name]?.finish
                ].filter(Number) as number[])
              : []
          }
        />
      )}
      <div style={{ overflow: "scroll", flex: 1 }} {...containerProps}>
        <div style={{ position: "relative", ...layoutSize }}>{items}</div>
      </div>
    </>
  );
};

interface Bounds {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

const boundsForBox = (a: GaantChartBox) => {
  return {
    minX: a.x,
    minY: a.y * BOX_HEIGHT,
    maxX: a.x + a.width,
    maxY: a.y * BOX_HEIGHT + BOX_HEIGHT
  };
};

const boundsForLine = (a: GaantChartBox, b: GaantChartBox) => {
  const minIdx = Math.min(a.y, b.y);
  const maxIdx = Math.max(a.y, b.y);

  const maxY = maxIdx * BOX_HEIGHT + BOX_MARGIN_Y;
  const minY = minIdx * BOX_HEIGHT + BOX_HEIGHT / 2;

  const minX = Math.min(a.x + a.width, b.x + b.width);
  const maxX =
    maxIdx === minIdx
      ? Math.max(a.x, b.x)
      : Math.max(a.x + a.width / 2, b.x + b.width / 2);

  return { minX, minY, maxX, maxY } as Bounds;
};

const GaantLine = React.memo(
  ({
    minX,
    minY,
    maxX,
    maxY,
    dotted,
    darkened,
    depIdx
  }: {
    dotted: boolean;
    darkened: boolean;
    depIdx: number;
  } & Bounds) => {
    const border = `${LINE_SIZE}px ${dotted ? "dotted" : "solid"} ${
      darkened ? Colors.DARK_GRAY1 : Colors.LIGHT_GRAY3
    }`;

    return (
      <>
        <div
          className="line"
          style={{
            height: 1,
            left: minX,
            width: dotted ? 50 : maxX + (depIdx % 10) * LINE_SIZE - minX,
            top: minY - 1,
            borderTop: border,
            zIndex: darkened ? 100 : 1
          }}
        />
        {minY !== maxY && !dotted && (
          <div
            className="line"
            style={{
              width: 1,
              left: maxX + (depIdx % 10) * LINE_SIZE,
              top: minY,
              height: maxY - minY,
              borderRight: border,
              zIndex: darkened ? 100 : 1
            }}
          />
        )}
      </>
    );
  },
  isEqual
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

  .dot {
    display: inline-block;
    position: absolute;
    width: ${BOX_DOT_SIZE}px;
    height: ${BOX_DOT_SIZE}px;
    border: 1px solid transparent;
    z-index: 2;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    border-radius: ${BOX_DOT_SIZE / 2}px;

    transition: top ${CSS_DURATION} linear, left ${CSS_DURATION} linear;
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

    &.focused {
      border: 1px solid ${Colors.DARK_GRAY1};
      box-shadow: 0 0 0 2px goldenrod;
    }
    &.hovered {
      border: 1px solid ${Colors.DARK_GRAY3};
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

const GaantChartModeControl: React.FunctionComponent<{
  value: GaantChartMode;
  hideTimedMode: boolean;
  onChange: (mode: GaantChartMode) => void;
}> = React.memo(({ value, onChange, hideTimedMode }) => (
  <ButtonGroup style={{ flexShrink: 0 }}>
    <Button
      key={GaantChartMode.FLAT}
      small={true}
      icon="column-layout"
      title={"Flat"}
      active={value === GaantChartMode.FLAT}
      onClick={() => onChange(GaantChartMode.FLAT)}
    />
    <Button
      key={GaantChartMode.WATERFALL}
      small={true}
      icon="gantt-chart"
      title={"Waterfall"}
      active={value === GaantChartMode.WATERFALL}
      onClick={() => onChange(GaantChartMode.WATERFALL)}
    />
    {!hideTimedMode && (
      <Button
        key={GaantChartMode.WATERFALL_TIMED}
        small={true}
        icon="time"
        rightIcon="gantt-chart"
        title={"Waterfall with Execution Timing"}
        active={value === GaantChartMode.WATERFALL_TIMED}
        onClick={() => onChange(GaantChartMode.WATERFALL_TIMED)}
      />
    )}
  </ButtonGroup>
));

/**
 * LogScaleSlider renders a horizontal slider that lets you adjust the graph timescale
 * from MIN_SCALE to MAX_SCALE on a log scale. It uses Blueprint CSS but not the Slider
 * component, becasue that renders twice and triggers a re-layout as it sizes itself.
 */
const LogScaleSlider: React.FunctionComponent<{
  value: number;
  onChange: (v: number) => void;
}> = React.memo(props => {
  const multiplier = (Math.log(MAX_SCALE) - Math.log(MIN_SCALE)) / 100;
  const value = (Math.log(props.value) - Math.log(MIN_SCALE)) / multiplier;
  const onChange = (v: number) =>
    props.onChange(Math.exp(Math.log(MIN_SCALE) + multiplier * v));

  return (
    <div
      className="bp3-slider bp3-slider-unlabeled"
      onMouseDown={(e: React.MouseEvent) => {
        const rect = e.currentTarget
          .closest(".bp3-slider")!
          .getBoundingClientRect();

        let initialX: number;
        if (
          e.target instanceof HTMLElement &&
          e.target.classList.contains("bp3-slider-handle")
        ) {
          initialX = e.pageX;
        } else {
          initialX = rect.left + (value / 100) * rect.width;
        }

        const onUpdate = (e: MouseEvent) => {
          const nextValue = value + (e.pageX - initialX) * (100 / rect.width);
          onChange(Math.max(0, Math.min(100, nextValue)));
        };
        const onRelease = (e: MouseEvent) => {
          onUpdate(e);
          document.removeEventListener("mousemove", onUpdate);
          document.removeEventListener("mouseup", onRelease);
        };
        document.addEventListener("mousemove", onUpdate);
        document.addEventListener("mouseup", onRelease);
      }}
    >
      <div className="bp3-slider-track">
        <div
          className="bp3-slider-progress"
          style={{ left: 0, right: 0, top: 0 }}
        />
        <div
          className="bp3-slider-progress bp3-intent-primary"
          style={{ left: 0, right: `${100 - value}%`, top: 0 }}
        />
      </div>
      <div className="bp3-slider-axis" />
      <span
        className="bp3-slider-handle"
        style={{ left: `calc(${value}% - 8px)` }}
        tabIndex={0}
      />
    </div>
  );
});
