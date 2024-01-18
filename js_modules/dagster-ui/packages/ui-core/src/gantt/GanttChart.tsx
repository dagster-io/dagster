import * as React from 'react';
import isEqual from 'lodash/isEqual';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {
  Box,
  Checkbox,
  FontFamily,
  Group,
  Icon,
  NonIdealState,
  Spinner,
  SpinnerWrapper,
  SplitPanelContainer,
  colorAccentCyan,
  colorAccentGray,
  colorAccentGrayHover,
  colorAccentReversed,
  colorAccentYellow,
  colorBackgroundCyan,
  colorBackgroundDefault,
  colorBackgroundGray,
  colorBackgroundYellow,
  colorFocusRing,
  colorTextYellow,
  useViewport,
} from '@dagster-io/ui-components';

import {AppContext} from '../app/AppContext';
import {GraphQueryItem, filterByQuery} from '../app/GraphQueryImpl';
import {withMiddleTruncation} from '../app/Util';
import {WebSocketContext} from '../app/WebSocketProvider';
import {CancelRunButton} from '../runs/RunActionButtons';
import {
  EMPTY_RUN_METADATA,
  IRunMetadataDict,
  IStepMetadata,
  IStepState,
} from '../runs/RunMetadataProvider';
import {runsPathWithFilters} from '../runs/RunsFilterInput';
import {StepSelection} from '../runs/StepSelection';
import {RunFragment} from '../runs/types/RunFragments.types';
import {GraphQueryInput} from '../ui/GraphQueryInput';
import {
  BOTTOM_INSET,
  BOX_DOT_MARGIN_Y,
  BOX_DOT_SIZE,
  BOX_DOT_WIDTH_CUTOFF,
  BOX_HEIGHT,
  BOX_MARGIN_Y,
  BOX_SHOW_LABEL_WIDTH_CUTOFF,
  BOX_SPACING_X,
  CSS_DURATION,
  DEFAULT_OPTIONS,
  GanttChartBox,
  GanttChartLayout,
  GanttChartLayoutOptions,
  GanttChartMode,
  GanttChartPlacement,
  GanttViewport,
  LINE_SIZE,
  MAX_SCALE,
  MIN_SCALE,
  TOP_INSET,
} from './Constants';
import {isDynamicStep} from './DynamicStepSupport';
import {
  BuildLayoutParams,
  adjustLayoutWithRunMetadata,
  boxStyleFor,
  buildLayout,
  interestingQueriesFor,
} from './GanttChartLayout';
import {GanttChartModeControl} from './GanttChartModeControl';
import {GanttChartTimescale} from './GanttChartTimescale';
import {GanttStatusPanel} from './GanttStatusPanel';
import {OptionsContainer, OptionsSpacer} from './VizComponents';
import {ZoomSlider} from './ZoomSlider';
import {useGanttChartMode} from './useGanttChartMode';

export {GanttChartMode} from './Constants';

const HIGHLIGHT_TIME_EVENT = 'gantt-highlight-time';

let highlightTimer: ReturnType<typeof setTimeout>;

/**
 * Set or clear the highlighted time on the Gantt chart. Goal of this convenience
 * method is to make the implementation (via event dispatch) private to this file.
 */
export function setHighlightedGanttChartTime(timestamp: null | string, debounced = true) {
  clearTimeout(highlightTimer);

  if (debounced) {
    highlightTimer = setTimeout(() => setHighlightedGanttChartTime(timestamp, false), 100);
  } else {
    document.dispatchEvent(new CustomEvent(HIGHLIGHT_TIME_EVENT, {detail: timestamp}));
  }
}

interface GanttChartProps {
  selection: StepSelection;
  focusedTime: number | null;
  runId: string;
  graph: GraphQueryItem[];
  options?: Partial<GanttChartLayoutOptions>;
  metadata?: IRunMetadataDict;
  toolbarActions?: React.ReactChild;

  onClickStep: (step: string, evt: React.MouseEvent<any>) => void;
  onSetSelection: (query: string) => void;

  // for storybooks
  overrideNowTime?: number;
}

interface GanttChartState {
  options: GanttChartLayoutOptions;
}

export const GanttChart = (props: GanttChartProps) => {
  const {graph, onSetSelection, options, selection, toolbarActions} = props;
  const [mode, setMode] = useGanttChartMode();
  const [state, setState] = React.useState(() => ({
    ...DEFAULT_OPTIONS,
    ...options,
    mode,
  }));

  const cachedLayout = React.useRef<GanttChartLayout | null>(null);
  const cachedLayoutParams = React.useRef<BuildLayoutParams | null>(null);
  const graphFiltered = filterByQuery(graph, selection.query);
  const layoutParams = React.useMemo(
    () => ({
      nodes: state.hideUnselectedSteps ? graphFiltered.all : graph,
      mode: state.mode,
    }),
    [graph, graphFiltered.all, state.hideUnselectedSteps, state.mode],
  );

  const layout = React.useMemo(() => {
    const names = (ns: GraphQueryItem[]) => ns.map((n) => n.name).join(',');
    if (
      !cachedLayoutParams.current ||
      names(cachedLayoutParams.current.nodes) !== names(layoutParams.nodes) ||
      cachedLayoutParams.current.mode !== layoutParams.mode
    ) {
      cachedLayout.current = buildLayout(layoutParams);
      cachedLayoutParams.current = layoutParams;
    }
    return cachedLayout.current!;
  }, [layoutParams]);

  const updateOptions = React.useCallback((changes: Partial<GanttChartLayoutOptions>) => {
    setState((current) => ({...current, ...changes}));
  }, []);

  const onChangeMode = React.useCallback(
    (mode: GanttChartMode) => {
      updateOptions({mode});
      setMode(mode);
    },
    [setMode, updateOptions],
  );

  const onUpdateQuery = React.useCallback(
    (query: string) => {
      onSetSelection(query || '*');
    },
    [onSetSelection],
  );

  const onDoubleClickStep = React.useCallback(
    (stepKey: string) => {
      const query = `*${stepKey}*`;
      onUpdateQuery(selection.query !== query ? query : '*');
    },
    [onUpdateQuery, selection.query],
  );

  return (
    <GanttChartContainer>
      <OptionsContainer>
        <GanttChartModeControl
          value={state.mode}
          onChange={onChangeMode}
          hideTimedMode={state.hideTimedMode}
        />
        {state.mode === GanttChartMode.WATERFALL_TIMED && (
          <>
            <OptionsSpacer />
            <div style={{width: 200}}>
              <ZoomSlider value={state.zoom} onChange={(v) => updateOptions({zoom: v})} />
            </div>
            <OptionsSpacer />
            <Checkbox
              style={{marginBottom: 0}}
              label="Hide not started steps"
              checked={state.hideWaiting}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                updateOptions({hideWaiting: e.target.checked})
              }
            />
          </>
        )}
        <div style={{flex: 1}} />
        {toolbarActions}
      </OptionsContainer>
      <GanttChartInner
        {...props}
        options={{...state}}
        layout={layout}
        graph={graph}
        onUpdateQuery={onUpdateQuery}
        onDoubleClickStep={onDoubleClickStep}
        onChange={() =>
          updateOptions({
            hideUnselectedSteps: !state.hideUnselectedSteps,
          })
        }
      />
    </GanttChartContainer>
  );
};

type GanttChartInnerProps = GanttChartProps &
  GanttChartState & {
    graph: GraphQueryItem[];
    layout: GanttChartLayout;
    onUpdateQuery: (value: string) => void;
    onDoubleClickStep: (stepName: string) => void;
    onChange: () => void;
  };

const GanttChartInner = (props: GanttChartInnerProps) => {
  const {viewport, containerProps, onMoveToViewport} = useViewport();
  const [hoveredStep, setHoveredNodeName] = React.useState<string | null>(null);
  const [hoveredTime, setHoveredTime] = React.useState<number | null>(null);
  const [nowMs, setNowMs] = React.useState<number>(() => props.overrideNowTime || Date.now());
  const {options, metadata, selection} = props;
  const animationRequest = React.useRef<number | null>(null);

  const {rootServerURI} = React.useContext(AppContext);

  const {availability, disabled, status} = React.useContext(WebSocketContext);
  const lostWebsocket = !disabled && availability === 'available' && status === WebSocket.CLOSED;

  // The slider in the UI updates `options.zoom` from 1-100. We convert that value
  // into a px-per-ms "scale", where the minimum is the value required to zoom-to-fit.
  // To make the slider feel more linear, we convert the input from log10 to logE.
  let minScale = MIN_SCALE;
  if (viewport.width && metadata && metadata.startedPipelineAt) {
    const zoomToFitWidthPx = Math.max(1, viewport.width - 150);
    const elapsedMs = Math.max(1, nowMs - metadata.startedPipelineAt);
    minScale = zoomToFitWidthPx / elapsedMs;
  }

  const scale = Math.exp(
    Math.log(minScale) + ((Math.log(MAX_SCALE) - Math.log(minScale)) / 100) * options.zoom,
  );

  const animate = React.useCallback(() => {
    setNowMs(props.overrideNowTime || Date.now());
    animationRequest.current = requestAnimationFrame(animate);
  }, [props.overrideNowTime]);

  const exitedAt = metadata?.exitedAt;

  // When the run is complete, stop the animation. We also do this when the WebSocket is lost,
  // since we would just be animating endlessly with no new logs.
  React.useEffect(() => {
    if (scale === 0 || lostWebsocket || exitedAt) {
      animationRequest.current && cancelAnimationFrame(animationRequest.current);
    }

    // Set the final timestamp.
    if (exitedAt) {
      setNowMs(exitedAt);
    }
  }, [scale, lostWebsocket, exitedAt]);

  // Kick off the Gantt animation. This will continue until the effect above determines that
  // the run is complete or that the connection is lost.
  React.useEffect(() => {
    animationRequest.current = requestAnimationFrame(animate);
    return () => {
      animationRequest.current && cancelAnimationFrame(animationRequest.current);
    };
  }, [animate]);

  // Listen for events specifying hover time (eg: a marker at a particular timestamp)
  // and sync them to our React state for display.
  React.useEffect(() => {
    const listener = (e: CustomEvent) => setHoveredTime(e.detail);
    document.addEventListener(HIGHLIGHT_TIME_EVENT, listener as EventListener);
    return () => document.removeEventListener(HIGHLIGHT_TIME_EVENT, listener as EventListener);
  });

  // The `layout` we receive has been laid out and the rows / "waterfall" are final,
  // but it doesn't incorporate the display scale or run metadata. We stretch and
  // shift the layout boxes using this data to create the final layout for display.
  const layout = adjustLayoutWithRunMetadata(
    props.layout,
    options,
    metadata || EMPTY_RUN_METADATA,
    scale,
    nowMs,
  );
  const layoutSize = {
    width: Math.max(0, ...layout.boxes.map((b) => b.x + b.width + BOX_SPACING_X)),
    height: Math.max(0, ...layout.boxes.map((b) => TOP_INSET + b.y * BOX_HEIGHT + BOTTOM_INSET)),
  };

  React.useEffect(() => {
    const node = layout.boxes.find((b) => selection.keys.includes(b.node.name));
    if (!node) {
      return;
    }
    const bounds = boundsForBox(node);
    const x = (bounds.maxX + bounds.minX) / 2 - viewport.width / 2;
    const y = (bounds.maxY + bounds.minY) / 2 - viewport.height / 2;
    onMoveToViewport({left: x, top: y}, true);
  }, [selection]); // eslint-disable-line

  const highlightedMs: number[] = [];
  if (props.focusedTime) {
    highlightedMs.push(props.focusedTime);
  }

  if (hoveredTime) {
    highlightedMs.push(hoveredTime);
  } else if (selection.keys.length > 0) {
    const selectedMeta = selection.keys
      .map((stepKey) => metadata?.steps[stepKey])
      .filter((x): x is IStepMetadata => x !== undefined);
    const sortedSelectedSteps = selectedMeta.sort((a, b) =>
      a.start && b.start ? a.start - b.start : 0,
    );
    const firstMeta = sortedSelectedSteps[0];
    const lastMeta = sortedSelectedSteps[sortedSelectedSteps.length - 1];
    if (firstMeta?.start) {
      highlightedMs.push(firstMeta.start);
    }
    if (lastMeta?.end) {
      highlightedMs.push(lastMeta.end);
    }
  }

  const measurementComplete = viewport.width > 0;

  const content = (
    <>
      {options.mode === GanttChartMode.WATERFALL_TIMED && measurementComplete && (
        <GanttChartTimescale
          scale={scale}
          viewport={viewport}
          layoutSize={layoutSize}
          startMs={metadata?.startedPipelineAt || 0}
          highlightedMs={highlightedMs}
          nowMs={nowMs}
        />
      )}
      <div style={{overflow: 'scroll', flex: 1}} {...containerProps}>
        <div style={{position: 'relative', marginBottom: 70, ...layoutSize}}>
          {measurementComplete && (
            <GanttChartViewportContents
              options={options}
              metadata={metadata || EMPTY_RUN_METADATA}
              layout={layout}
              hoveredStep={hoveredStep}
              focusedSteps={selection.keys}
              viewport={viewport}
              setHoveredNodeName={setHoveredNodeName}
              onClickStep={props.onClickStep}
              onDoubleClickStep={props.onDoubleClickStep}
            />
          )}
        </div>
      </div>

      <GraphQueryInputContainer>
        {lostWebsocket ? (
          <WebsocketWarning>
            <Box flex={{justifyContent: 'space-around'}} margin={{bottom: 12}}>
              <Group
                direction="row"
                spacing={8}
                background={colorBackgroundYellow()}
                padding={{vertical: 8, horizontal: 12}}
                alignItems="flex-start"
              >
                <Icon name="warning" color={colorAccentYellow()} />
                <div style={{maxWidth: '400px', whiteSpace: 'normal', overflow: 'hidden'}}>
                  <strong>Lost connection to Dagster webserver.</strong>
                  <span>
                    {` Verify that your instance is responding to requests at ${rootServerURI} and reload the page.`}
                  </span>
                </div>
              </Group>
            </Box>
          </WebsocketWarning>
        ) : null}
        <FilterInputsBackgroundBox flex={{direction: 'row', alignItems: 'center', gap: 12}}>
          <GraphQueryInput
            items={props.graph}
            value={props.selection.query}
            placeholder="Type a step subset"
            onChange={props.onUpdateQuery}
            presets={metadata ? interestingQueriesFor(metadata, layout) : undefined}
            className={selection.keys.length > 0 ? 'has-step' : ''}
          />
          <Checkbox
            checked={options.hideUnselectedSteps}
            label="Hide unselected steps"
            onChange={props.onChange}
          />
        </FilterInputsBackgroundBox>
      </GraphQueryInputContainer>
    </>
  );

  return metadata ? (
    <SplitPanelContainer
      identifier="gantt-split"
      axis="horizontal"
      first={content}
      firstInitialPercent={70}
      second={
        <GanttStatusPanel
          {...props}
          nowMs={nowMs}
          metadata={metadata}
          onHighlightStep={(name) => setHoveredNodeName(name)}
        />
      }
    />
  ) : (
    content
  );
};

interface GanttChartViewportContentsProps {
  options: GanttChartLayoutOptions;
  metadata: IRunMetadataDict;
  layout: GanttChartLayout;
  hoveredStep: string | null;
  focusedSteps: string[];
  viewport: GanttViewport;
  setHoveredNodeName: (name: string | null) => void;
  onDoubleClickStep: (step: string) => void;
  onClickStep: (step: string, evt: React.MouseEvent<any>) => void;
}

const GanttChartViewportContents = (props: GanttChartViewportContentsProps) => {
  const {viewport, layout, hoveredStep, focusedSteps, metadata, options} = props;
  const items: React.ReactChild[] = [];

  // To avoid drawing zillions of DOM nodes, we render only the boxes + lines that
  // intersect with the current viewport.
  const intersectsViewport = (bounds: Bounds) =>
    bounds.minX < viewport.left + viewport.width &&
    bounds.maxX > viewport.left &&
    bounds.minY < viewport.top + viewport.height &&
    bounds.maxY > viewport.top;

  // We track the number of lines that end at each X value (they go over and then down,
  // so this tracks where the vertical lines are). We shift lines by {count}px if there
  // are others at the same X so wide "tracks" show you where data is being collected.
  const verticalLinesAtXCoord: {[x: string]: number} = {};

  if (options.mode !== GanttChartMode.FLAT) {
    layout.boxes.forEach((box) => {
      box.children.forEach((child, childIdx) => {
        const bounds = boundsForLine(box, child);
        if (!intersectsViewport(bounds)) {
          return;
        }
        const childNotDrawn = !layout.boxes.includes(child);
        const childWaiting = metadata ? !metadata.steps[child.node.name]?.state : false;

        const overlapAtXCoord = verticalLinesAtXCoord[bounds.maxX] || 0;
        verticalLinesAtXCoord[bounds.maxX] = overlapAtXCoord + 1;

        items.push(
          <GanttLine
            darkened={
              (focusedSteps?.includes(box.node.name) || hoveredStep) === box.node.name ||
              (focusedSteps?.includes(child.node.name) || hoveredStep) === child.node.name
            }
            dotted={childNotDrawn || childWaiting}
            key={`${box.key}-${child.key}-${childIdx}`}
            depNotDrawn={childNotDrawn}
            depIdx={overlapAtXCoord}
            {...bounds}
          />,
        );
      });
    });
  }

  layout.boxes.forEach((box) => {
    const bounds = boundsForBox(box);
    const useDot = box.width === BOX_DOT_WIDTH_CUTOFF;
    if (!intersectsViewport(bounds)) {
      return;
    }

    items.push(
      <div
        key={box.key}
        data-tooltip={box.node.name}
        onClick={(evt: React.MouseEvent<any>) => props.onClickStep(box.node.name, evt)}
        onDoubleClick={() => props.onDoubleClickStep(box.node.name)}
        onMouseEnter={() => props.setHoveredNodeName(box.node.name)}
        onMouseLeave={() => props.setHoveredNodeName(null)}
        className={`
            chart-element
            ${useDot ? 'dot' : 'box'}
            ${focusedSteps.includes(box.node.name) && 'focused'}
            ${hoveredStep === box.node.name && 'hovered'}
            ${isDynamicStep(box.node.name) && 'dynamic'}`}
        style={{
          left: bounds.minX,
          top: bounds.minY + (useDot ? BOX_DOT_MARGIN_Y : BOX_MARGIN_Y),
          width: useDot ? BOX_DOT_SIZE : box.width,
          ...boxStyleFor(box.state, {metadata, options}),
        }}
      >
        {box.state === IStepState.RUNNING ? <Spinner purpose="body-text" /> : undefined}
        {truncatedBoxLabel(box)}
      </div>,
    );
  });

  if (options.mode === GanttChartMode.WATERFALL_TIMED) {
    // Note: We sort the markers from left to right so that they're added to the DOM in that
    // order and a long one doesn't make ones "behind it" unclickable.
    layout.markers
      .map((marker, idx) => ({marker, idx, bounds: boundsForBox(marker)}))
      .filter(({bounds}) => intersectsViewport(bounds))
      .sort((a, b) => a.bounds.minX - b.bounds.minX)
      .forEach(({marker, bounds, idx}) => {
        const useDot = marker.width === BOX_DOT_WIDTH_CUTOFF;

        items.push(
          <div
            key={idx}
            data-tooltip={marker.key}
            className={`
            chart-element
            ${useDot ? 'marker-dot' : 'marker-whiskers'}`}
            style={{
              left: bounds.minX,
              top: bounds.minY + (useDot ? BOX_DOT_MARGIN_Y : BOX_MARGIN_Y),
              width: useDot ? BOX_DOT_SIZE : marker.width,
            }}
          >
            <div />
          </div>,
        );
      });
  }

  return <>{items}</>;
};

interface Bounds {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

/**
 * Returns the top left + bottom right bounds for the provided Gantt chart box
 * so that the box can be drawn and tested for intersection with the viewport.
 */
const boundsForBox = (a: GanttChartPlacement): Bounds => {
  return {
    minX: a.x,
    minY: TOP_INSET + a.y * BOX_HEIGHT,
    maxX: a.x + a.width,
    maxY: TOP_INSET + a.y * BOX_HEIGHT + BOX_HEIGHT,
  };
};

/**
 * Returns the top left + bottom right bounds for the line between two Gantt
 * chart boxes. The boxes do not need to be provided in left -> right order.
 * @param a: GanttChartBox
 */
const boundsForLine = (a: GanttChartBox, b: GanttChartBox): Bounds => {
  if (b.y < a.y) {
    [a, b] = [b, a];
  }

  const aIsDot = a.width === BOX_DOT_WIDTH_CUTOFF;
  const aCenterY = aIsDot ? BOX_DOT_MARGIN_Y + BOX_DOT_SIZE / 2 : BOX_HEIGHT / 2;

  const bIsDot = b.width === BOX_DOT_WIDTH_CUTOFF;
  const bCenterY = bIsDot ? BOX_DOT_MARGIN_Y + BOX_DOT_SIZE / 2 : BOX_HEIGHT / 2;

  const straight = b.y === a.y;

  // Line comes out of the center of the right side of the box
  const minX = Math.min(a.x + a.width, b.x + b.width);
  const minY = TOP_INSET + (straight ? a.y * BOX_HEIGHT + aCenterY : a.y * BOX_HEIGHT + aCenterY);

  // Line ends on the center left edge of the box if it is on the
  // same line, or drops into the top center of the box if it's below.
  const maxX = straight
    ? Math.max(a.x, b.x)
    : Math.max(a.x + a.width / 2, b.x + (bIsDot ? BOX_DOT_SIZE : b.width) / 2);
  const maxY = straight
    ? TOP_INSET + b.y * BOX_HEIGHT + bCenterY
    : TOP_INSET + b.y * BOX_HEIGHT + (bIsDot ? BOX_DOT_MARGIN_Y : BOX_MARGIN_Y);

  return {minX, minY, maxX, maxY};
};

/**
 * Renders a line on the Gantt visualization using a thin horizontal <div> and
 * a thin vertical <div> as necessary.
 */
const GanttLine = React.memo(
  ({
    minX,
    minY,
    maxX,
    maxY,
    dotted,
    darkened,
    depIdx,
    depNotDrawn,
  }: {
    dotted: boolean;
    darkened: boolean;
    depIdx: number;
    depNotDrawn: boolean;
  } & Bounds) => {
    const border = `${LINE_SIZE}px ${dotted ? 'dotted' : 'solid'} ${
      darkened ? colorAccentGray() : colorAccentGrayHover()
    }`;

    const maxXAvoidingOverlap = maxX + (depIdx % 10) * LINE_SIZE;

    return (
      <>
        <div
          className="line"
          style={{
            height: 1,
            left: minX,
            width: depNotDrawn ? 50 : maxXAvoidingOverlap - minX,
            top: minY - 1,
            borderTop: border,
            zIndex: darkened ? 100 : 1,
          }}
        />
        {minY !== maxY && !depNotDrawn && (
          <div
            className="line"
            style={{
              width: 1,
              left: maxXAvoidingOverlap,
              top: minY - LINE_SIZE / 2,
              height: maxY - minY,
              borderRight: border,
              zIndex: darkened ? 100 : 1,
            }}
          />
        )}
      </>
    );
  },
  isEqual,
);

function truncatedBoxLabel(box: GanttChartBox) {
  if (box.width <= BOX_SHOW_LABEL_WIDTH_CUTOFF) {
    return undefined;
  }

  // Note: The constants here must be in sync with the CSS immediately below
  const totalPadding = 7 + (box.state === IStepState.RUNNING ? 16 : 0);
  const maxLength = (box.width - totalPadding) / 6.2;

  return withMiddleTruncation(box.node.name, {maxLength});
}

// Note: It is much faster to use standard CSS class selectors here than make
// each box and line a styled-component because all styled components register
// listeners for the "theme" React context.
const GanttChartContainer = styled.div`
  height: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  z-index: 2;
  user-select: none;
  background: ${colorBackgroundDefault()};

  .line {
    position: absolute;
    user-select: none;
    pointer-events: none;
    transition:
      top ${CSS_DURATION}ms linear,
      left ${CSS_DURATION}ms linear,
      width ${CSS_DURATION}ms linear,
      height ${CSS_DURATION}ms linear;
  }

  .chart-element {
    font-size: 12px;
    transition:
      top ${CSS_DURATION}ms linear,
      left ${CSS_DURATION}ms linear;
    display: inline-block;
    position: absolute;
    color: ${colorAccentReversed()};
    overflow: hidden;
    user-select: text;
    z-index: 2;

    user-select: none;
    -webkit-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
  }

  .dot {
    width: ${BOX_DOT_SIZE}px;
    height: ${BOX_DOT_SIZE}px;
    border: 1px solid transparent;
    border-radius: ${BOX_DOT_SIZE / 2}px;
  }

  .box {
    /* Note: padding + font changes may also impact truncatedBoxLabel */

    height: ${BOX_HEIGHT - BOX_MARGIN_Y * 2}px;
    padding: 3px;
    padding-right: 1px;
    border-radius: 2px;
    white-space: nowrap;
    font-family: ${FontFamily.monospace};
    font-size: 12.5px;
    font-weight: 700;
    line-height: 15px;

    transition:
      top ${CSS_DURATION}ms linear,
      left ${CSS_DURATION}ms linear,
      width ${CSS_DURATION}ms linear,
      height ${CSS_DURATION}ms linear,
      box-shadow ${CSS_DURATION}ms linear;

    &.focused {
      box-shadow: 0 0 0 2px ${colorFocusRing()};
    }
    &.hovered {
      box-shadow: 0 0 0 2px ${colorFocusRing()};
    }
    &.dynamic {
      filter: brightness(115%);
    }

    ${SpinnerWrapper} {
      display: inline-block;
      vertical-align: text-bottom;
      padding-right: 4px;
    }
  }

  .marker-dot {
    width: ${BOX_DOT_SIZE}px;
    height: ${BOX_DOT_SIZE}px;
    border: 1px solid ${colorAccentCyan()};
    border-radius: ${BOX_DOT_SIZE / 2}px;
  }

  .marker-whiskers {
    display: inline-block;
    position: absolute;
    height: ${BOX_HEIGHT - BOX_MARGIN_Y * 2}px;
    background-color: ${colorBackgroundCyan()};
    border-left: 1px solid ${colorAccentCyan()};
    border-right: 1px solid ${colorAccentCyan()};
    transition:
      top ${CSS_DURATION}ms linear,
      left ${CSS_DURATION}ms linear,
      width ${CSS_DURATION}ms linear;

    & > div {
      border-bottom: 1px dashed ${colorAccentCyan()};
      height: ${(BOX_HEIGHT - BOX_MARGIN_Y * 2) / 2}px;
    }
  }
`;

const WebsocketWarning = styled.div`
  position: absolute;
  bottom: 100%;
  color: ${colorTextYellow()};
  width: 100%;
`;

const GraphQueryInputContainer = styled.div`
  z-index: 2;
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
`;

const FilterInputsBackgroundBox = styled(Box)`
  background-color: ${colorBackgroundGray()};
  border-radius: 4px;
  padding: 8px 12px 8px 8px;
`;

export const GanttChartLoadingState = ({runId}: {runId: string}) => (
  <GanttChartContainer>
    <OptionsContainer />
    <SplitPanelContainer
      identifier="gantt-split"
      axis="horizontal"
      first={
        <div style={{margin: 'auto', marginTop: 100}}>
          <Spinner purpose="section" />
        </div>
      }
      firstInitialPercent={70}
      second={
        <GanttStatusPanel
          graph={[]}
          metadata={EMPTY_RUN_METADATA}
          selection={{keys: [], query: '*'}}
          runId={runId}
          nowMs={0}
        />
      }
    />
  </GanttChartContainer>
);

export const QueuedState = ({run}: {run: RunFragment}) => (
  <GanttChartContainer>
    <OptionsContainer style={{justifyContent: 'flex-end'}}>
      <CancelRunButton run={run} />
    </OptionsContainer>
    <SplitPanelContainer
      identifier="gantt-split"
      axis="horizontal"
      first={
        <NonIdealState
          icon="arrow_forward"
          title="Run queued"
          description="This run is queued for execution and will start soon."
          action={
            <Link to={runsPathWithFilters([{token: 'status', value: 'QUEUED'}])}>
              View queued runs
            </Link>
          }
        />
      }
      firstInitialPercent={70}
      second={
        <GanttStatusPanel
          graph={[]}
          metadata={EMPTY_RUN_METADATA}
          selection={{keys: [], query: '*'}}
          runId={run.id}
          nowMs={0}
        />
      }
    />
  </GanttChartContainer>
);
