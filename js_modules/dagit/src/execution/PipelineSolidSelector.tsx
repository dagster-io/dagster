import { Colors, Button, Classes, Dialog } from "@blueprintjs/core";
import * as React from "react";
import gql from "graphql-tag";
import PipelineGraph from "../graph/PipelineGraph";
import { QueryResult, Query } from "react-apollo";
import {
  PipelineExecutionRootQuery,
  PipelineExecutionRootQuery_pipeline
} from "./types/PipelineExecutionRootQuery";
import Loading from "../Loading";
import {
  getDagrePipelineLayout,
  layoutsIntersect,
  pointsToBox
} from "../graph/getFullSolidLayout";
import SVGViewport from "../graph/SVGViewport";

interface IPipelineSolidSelectorProps {
  pipelineName: string;
  value: string[];
  onChange: (value: string[]) => void;
}

interface IPipelineSolidSelectorInnerProps extends IPipelineSolidSelectorProps {
  pipeline: PipelineExecutionRootQuery_pipeline;
}

interface IPipelineSolidSelectorState {
  // True if the modal is open
  open: boolean;

  // The list of solids currently highlighted in the modal.
  // (The solidSubset value to be committed upon close.)
  highlighted: string[];

  // The start / stop of the marquee selection tool
  toolRectStart: null | { x: number; y: number };
  toolRectEnd: null | { x: number; y: number };
}

class PipelineSolidSelector extends React.Component<
  IPipelineSolidSelectorInnerProps,
  IPipelineSolidSelectorState
> {
  static fragments = {
    PipelineSolidSelectorFragment: gql`
      fragment PipelineSolidSelectorFragment on Pipeline {
        ...PipelineGraphFragment
      }
    `
  };

  state: IPipelineSolidSelectorState = {
    open: false,
    highlighted: [],
    toolRectStart: null,
    toolRectEnd: null
  };

  handleClickSolid = (solidName: string) => {
    const { highlighted } = this.state;

    if (highlighted.indexOf(solidName) !== -1) {
      this.setState({ highlighted: highlighted.filter(s => s !== solidName) });
    } else {
      this.setState({ highlighted: [...highlighted, solidName] });
    }
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
    const highlighted = Object.keys(layout.solids).filter(name =>
      layoutsIntersect(svgToolBox, layout.solids[name].boundingBox)
    );

    this.setState({
      toolRectEnd: null,
      toolRectStart: null,
      highlighted
    });
  };

  handleOpen = () => {
    this.setState({ open: true, highlighted: this.props.value });
  };

  handleSave = () => {
    this.props.onChange(this.state.highlighted);
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
          title={"Select Solids"}
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
              onClickSolid={this.handleClickSolid}
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
        <a onClick={this.handleOpen}>
          {this.props.value.length ? this.props.value.join(", ") : "All Solids"}
        </a>
      </div>
    );
  }
}

export const PIPELINE_SOLID_SELECTOR_QUERY = gql`
  query PipelineSolidSelectorQuery($name: String!) {
    pipeline(name: $name) {
      name
      ...PipelineGraphFragment
    }
  }
  ${PipelineGraph.fragments.PipelineGraphFragment}
`;

export default (props: IPipelineSolidSelectorProps) => (
  <Query
    query={PIPELINE_SOLID_SELECTOR_QUERY}
    variables={{ name: props.pipelineName }}
  >
    {(queryResult: QueryResult<PipelineExecutionRootQuery, any>) => (
      <Loading queryResult={queryResult}>
        {result => (
          <PipelineSolidSelector {...props} pipeline={result.pipeline} />
        )}
      </Loading>
    )}
  </Query>
);
