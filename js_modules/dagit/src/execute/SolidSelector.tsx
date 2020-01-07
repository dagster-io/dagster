import {
  Colors,
  Button,
  Classes,
  Dialog,
  Intent,
  Spinner
} from "@blueprintjs/core";
import * as React from "react";
import gql from "graphql-tag";
import PipelineGraph from "../graph/PipelineGraph";
import { useQuery } from "react-apollo";
import {
  SolidSelectorQuery,
  SolidSelectorQuery_pipeline,
  SolidSelectorQuery_pipeline_solids
} from "./types/SolidSelectorQuery";
import { IconNames } from "@blueprintjs/icons";
import { SubsetError } from "./ExecutionSessionContainer";
import {
  getDagrePipelineLayout,
  layoutsIntersect,
  pointsToBox
} from "../graph/getFullSolidLayout";
import SVGViewport from "../graph/SVGViewport";
import { ShortcutHandler } from "../ShortcutHandler";

interface ISolidSelectorProps {
  pipelineName: string;
  subsetError: SubsetError;
  value: string[] | null;
  label: string | null;
  onChange: (value: string[] | null, label: string | null) => void;
  onRequestClose?: () => void;
}

interface ISolidSelectorInnerProps extends ISolidSelectorProps {
  pipeline: SolidSelectorQuery_pipeline | null;
}

interface ISolidSelectorState {
  // The list of solids currently highlighted in the modal.
  // (The solidSubset value to be committed upon close.)
  highlighted: string[];

  // The start / stop of the marquee selection tool
  toolRectStart: null | { x: number; y: number };
  toolRectEnd: null | { x: number; y: number };
}

function subsetDescription(
  solidSubset: string[] | null,
  pipeline: SolidSelectorQuery_pipeline | null
) {
  if (
    !solidSubset ||
    solidSubset.length === 0 ||
    (pipeline && solidSubset.length === pipeline.solids.length)
  ) {
    return "All Solids";
  }

  if (solidSubset.length === 1) {
    return solidSubset[0];
  }

  // try to find a start solid that can get us to all the solids without
  // any others in the path, indicating that an range label (eg "A -> B")
  // would fit. TODO: Bidirectional A-star?!
  const rangeDescription =
    pipeline &&
    solidSubset
      .map(startName => {
        let solidName = startName;
        let rest = solidSubset.filter(s => s !== solidName);

        const nameMatch = (s: SolidSelectorQuery_pipeline_solids) =>
          s.name === solidName;

        const downstreamSolidSearch = (n: string) => rest.indexOf(n) !== -1;

        while (rest.length > 0) {
          const solid = pipeline.solids.find(nameMatch);
          if (!solid) return false;

          const downstreamSolidNames = solid.outputs.reduce(
            (v: string[], o) => v.concat(o.dependedBy.map(s => s.solid.name)),
            []
          );

          const nextSolidName = downstreamSolidNames.find(
            downstreamSolidSearch
          );
          if (!nextSolidName) return false;
          rest = rest.filter(s => s !== nextSolidName);
          solidName = nextSolidName;
        }
        return `${startName} → ${solidName}`;
      })
      .find(n => n !== false);

  if (rangeDescription) {
    return rangeDescription;
  }
  return `${solidSubset.length} solids`;
}

const SolidSelectorModalContainer = (props: ISolidSelectorProps) => {
  const { data } = useQuery<SolidSelectorQuery>(SOLID_SELECTOR_QUERY, {
    variables: { name: props.pipelineName }
  });

  if (data?.pipeline?.__typename !== "Pipeline") {
    return (
      <div
        style={{
          height: `calc(100% - 85px)`,
          display: "flex",
          justifyContent: "center"
        }}
      >
        <div style={{ alignSelf: "center" }}>
          <Spinner size={32} />
        </div>
      </div>
    );
  }

  return (
    <>
      <SolidSelectorModal pipeline={data.pipeline} {...props} />
    </>
  );
};

class SolidSelectorModal extends React.PureComponent<
  ISolidSelectorInnerProps,
  ISolidSelectorState
> {
  state: ISolidSelectorState = {
    highlighted: [],
    toolRectStart: null,
    toolRectEnd: null
  };

  componentDidMount() {
    if (this.props.pipeline) {
      this.handleOpen(this.props);
    }
  }
  handleSVGMouseDown = (
    viewport: SVGViewport,
    event: React.MouseEvent<HTMLDivElement>
  ) => {
    const point = viewport.getOffsetXY(event);
    this.setState({ toolRectStart: point, toolRectEnd: point });

    const onMove = (event: MouseEvent) => {
      this.setState({ toolRectEnd: viewport.getOffsetXY(event) });
    };
    const onUp = () => {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
      this.handleSelectSolidsInToolRect(viewport);
    };

    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
    event.stopPropagation();
  };

  handleSelectSolidsInToolRect = (viewport: SVGViewport) => {
    const layout = getDagrePipelineLayout(
      this.props.pipeline ? this.props.pipeline.solids : []
    );
    const { toolRectEnd, toolRectStart } = this.state;
    if (!toolRectEnd || !toolRectStart) return;

    // Convert the tool rectangle to SVG coords
    const svgToolBox = pointsToBox(
      viewport.screenToSVGCoords(toolRectStart),
      viewport.screenToSVGCoords(toolRectEnd)
    );
    let highlighted = Object.keys(layout.solids).filter(name =>
      layoutsIntersect(svgToolBox, layout.solids[name].boundingBox)
    );

    // If you clicked a single solid, toggle the selection. Otherwise,
    // we blow away the ccurrently highlighted solids in favor of the new selection
    if (
      highlighted.length === 1 &&
      toolRectEnd.x === toolRectStart.x &&
      toolRectEnd.y === toolRectStart.y
    ) {
      const clickedSolid = highlighted[0];
      if (this.state.highlighted.indexOf(clickedSolid) !== -1) {
        highlighted = this.state.highlighted.filter(s => s !== clickedSolid);
      } else {
        highlighted = [...this.state.highlighted, clickedSolid];
      }
    }

    this.setState({
      toolRectEnd: null,
      toolRectStart: null,
      highlighted
    });
  };

  // Note: Having no elements highlighted means the entire pipeline executes.
  // The equivalent solidSubset is `null`, not `[]`, so we do some conversion here.

  handleOpen = (props: ISolidSelectorInnerProps) => {
    const { value, pipeline } = props;
    const valid = (value || []).filter(
      name => pipeline && !!pipeline.solids.find(s => s.name === name)
    );
    this.setState({ highlighted: valid });
  };

  handleSave = () => {
    const { highlighted } = this.state;
    this.props.onChange(
      highlighted.length > 0 ? [...highlighted] : null,
      subsetDescription(highlighted, this.props.pipeline)
    );
    this.setState({ highlighted: [] });
  };

  render() {
    const { pipeline } = this.props;
    const { highlighted, toolRectEnd, toolRectStart } = this.state;

    const allSolidsSelected =
      !highlighted.length ||
      !pipeline ||
      highlighted.length === pipeline.solids.length;

    return (
      <>
        <div
          className={Classes.DIALOG_BODY}
          style={{
            margin: 0,
            marginBottom: 17,
            height: `calc(100% - 85px)`
          }}
        >
          <PipelineGraph
            backgroundColor={Colors.LIGHT_GRAY5}
            pipelineName={pipeline ? pipeline.name : ""}
            solids={pipeline ? pipeline.solids : []}
            interactor={{
              onMouseDown: this.handleSVGMouseDown,
              onWheel: () => {},
              render: () => {
                if (!toolRectEnd || !toolRectStart) return null;
                const box = pointsToBox(toolRectEnd, toolRectStart);
                return (
                  <div
                    style={{
                      position: "absolute",
                      border: `1px dashed ${Colors.GRAY3}`,
                      left: box.x,
                      top: box.y,
                      width: box.width,
                      height: box.height
                    }}
                  />
                );
              }
            }}
            layout={getDagrePipelineLayout(
              pipeline && pipeline.solids ? pipeline.solids : []
            )}
            focusSolids={[]}
            highlightedSolids={
              pipeline
                ? pipeline.solids.filter(
                    (s: any) => highlighted.indexOf(s.name) !== -1
                  )
                : []
            }
          />
        </div>
        <div className={Classes.DIALOG_FOOTER}>
          <div className={Classes.DIALOG_FOOTER_ACTIONS}>
            <div style={{ alignSelf: "center" }}>
              {allSolidsSelected ? "All" : highlighted.length} solid
              {highlighted.length !== 1 || allSolidsSelected ? "s" : ""}{" "}
              selected
            </div>

            <Button onClick={this.close}>Cancel</Button>
            <Button intent="primary" onClick={this.handleSave}>
              Apply
            </Button>
          </div>
        </div>
      </>
    );
  }

  close = () => {
    this.props.onRequestClose && this.props.onRequestClose();
  };
}

export const SOLID_SELECTOR_QUERY = gql`
  query SolidSelectorQuery($name: String!) {
    pipeline(params: { name: $name }) {
      name
      solids {
        name
        ...PipelineGraphSolidFragment
      }
    }
  }
  ${PipelineGraph.fragments.PipelineGraphSolidFragment}
`;

export default (props: ISolidSelectorProps) => {
  const { subsetError, value, label } = props;
  const [open, setOpen] = React.useState(false);

  const onRequestClose = () => setOpen(false);

  let buttonText;
  if (subsetError) {
    buttonText = "Invalid Solid Selection";
  } else if (!value) {
    buttonText = "All Solids";
  } else if (value && label) {
    buttonText = label;
  } else {
    buttonText = subsetDescription(value, null);
  }

  return (
    <div>
      <ShortcutHandler
        shortcutLabel={"⌥S"}
        shortcutFilter={e => e.keyCode === 83 && e.altKey}
        onShortcut={() => setOpen(true)}
      >
        <Dialog
          icon="info-sign"
          onClose={() => setOpen(false)}
          style={{ width: "80vw", maxWidth: 1400, height: "80vh" }}
          title={"Select Solids to Execute"}
          usePortal={true}
          isOpen={open}
        >
          <SolidSelectorModalContainer
            {...props}
            onRequestClose={onRequestClose}
          />
        </Dialog>
        <Button
          icon={subsetError ? IconNames.WARNING_SIGN : IconNames.SEARCH_AROUND}
          intent={subsetError ? Intent.WARNING : Intent.NONE}
          onClick={() => setOpen(true)}
        >
          {buttonText}
        </Button>
      </ShortcutHandler>
    </div>
  );
};
