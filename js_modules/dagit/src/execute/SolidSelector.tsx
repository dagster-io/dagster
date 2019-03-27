import { Colors, Button, Classes, Dialog } from "@blueprintjs/core";
import * as React from "react";
import gql from "graphql-tag";
import PipelineGraph from "../graph/PipelineGraph";
import { QueryResult, Query } from "react-apollo";
import {
  SolidSelectorQuery,
  SolidSelectorQuery_pipeline
} from "./types/SolidSelectorQuery";
import Loading from "../Loading";
import {
  getDagrePipelineLayout,
  layoutsIntersect,
  pointsToBox
} from "../graph/getFullSolidLayout";
import SVGViewport from "../graph/SVGViewport";
import { IconNames } from "@blueprintjs/icons";

interface ISolidSelectorProps {
  pipelineName: string;
  value: string[] | null;
  onChange: (value: string[] | null) => void;
}

interface ISolidSelectorInnerProps extends ISolidSelectorProps {
  pipeline: SolidSelectorQuery_pipeline;
}

interface ISolidSelectorState {
  // True if the modal is open
  open: boolean;

  // The list of solids currently highlighted in the modal.
  // (The solidSubset value to be committed upon close.)
  highlighted: string[];

  // The start / stop of the marquee selection tool
  toolRectStart: null | { x: number; y: number };
  toolRectEnd: null | { x: number; y: number };
}

function subsetDescription(
  solidSubset: string[] | null,
  pipeline: SolidSelectorQuery_pipeline
) {
  if (
    !solidSubset ||
    solidSubset.length === 0 ||
    solidSubset.length === pipeline.solids.length
  ) {
    return "All Solids";
  }
  if (solidSubset.length === 1) {
    return solidSubset[0];
  }

  // try to find a start solid that can get us to all the solids without
  // any others in the path, indicating that an range label (eg "A -> B")
  // would fit. TODO: Bidirectional A-star?!
  const rangeDescription = solidSubset
    .map(startName => {
      let solidName = startName;
      let rest = solidSubset.filter(s => s !== solidName);

      while (rest.length > 0) {
        const solid = pipeline.solids.find(s => s.name === solidName);
        if (!solid) return false;

        const downstreamSolidNames = solid.outputs.reduce(
          (v: string[], o) => v.concat(o.dependedBy.map(s => s.solid.name)),
          []
        );

        const nextSolidName = downstreamSolidNames.find(
          n => rest.indexOf(n) !== -1
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

class SolidSelector extends React.PureComponent<
  ISolidSelectorInnerProps,
  ISolidSelectorState
> {
  state: ISolidSelectorState = {
    open: false,
    highlighted: [],
    toolRectStart: null,
    toolRectEnd: null
  };

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
    const layout = getDagrePipelineLayout(this.props.pipeline);
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

  handleOpen = () => {
    this.setState({ open: true, highlighted: this.props.value || [] });
  };

  handleSave = () => {
    const { highlighted } = this.state;
    this.props.onChange(highlighted.length > 0 ? highlighted : null);
    this.setState({ open: false, highlighted: [] });
  };

  render() {
    const { pipeline } = this.props;
    const { open, highlighted, toolRectEnd, toolRectStart } = this.state;

    return (
      <div>
        <Dialog
          icon="info-sign"
          onClose={() => this.setState({ open: false })}
          style={{ width: "80vw", maxWidth: 1400, height: "80vh" }}
          title={"Select Solids to Execute"}
          usePortal={true}
          isOpen={open}
        >
          <div
            className={Classes.DIALOG_BODY}
            style={{
              margin: 0,
              marginBottom: 17,
              height: `calc(100% - 85px)`
            }}
          >
            <PipelineGraph
              pipeline={pipeline}
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
              layout={getDagrePipelineLayout(pipeline)}
              highlightedSolids={pipeline.solids.filter(
                (s: any) => highlighted.indexOf(s.name) !== -1
              )}
            />
          </div>
          <div className={Classes.DIALOG_FOOTER}>
            <div className={Classes.DIALOG_FOOTER_ACTIONS}>
              <div style={{ alignSelf: "center" }}>
                {highlighted.length || "All"} solid
                {highlighted.length !== 1 ? "s" : ""} selected
              </div>
              <Button onClick={() => this.setState({ open: false })}>
                Cancel
              </Button>
              <Button intent="primary" onClick={this.handleSave}>
                Apply
              </Button>
            </div>
          </div>
        </Dialog>
        <Button icon={IconNames.SEARCH_AROUND} onClick={this.handleOpen}>
          {subsetDescription(this.props.value, this.props.pipeline)}
        </Button>
      </div>
    );
  }
}

export const SOLID_SELECTOR_QUERY = gql`
  query SolidSelectorQuery($name: String!) {
    pipeline(params: { name: $name }) {
      name
      solids {
        name
      }
      ...PipelineGraphFragment
    }
  }
  ${PipelineGraph.fragments.PipelineGraphFragment}
`;

export default (props: ISolidSelectorProps) => (
  <Query query={SOLID_SELECTOR_QUERY} variables={{ name: props.pipelineName }}>
    {(queryResult: QueryResult<SolidSelectorQuery, any>) => (
      <Loading queryResult={queryResult}>
        {result => <SolidSelector {...props} pipeline={result.pipeline} />}
      </Loading>
    )}
  </Query>
);
