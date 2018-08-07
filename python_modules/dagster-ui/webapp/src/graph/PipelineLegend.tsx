import * as React from "react";
import { LegendOrdinal } from "@vx/legend";
import PipelineColorScale from "./PipelineColorScale";

export default class PipelineLegend extends React.Component {
  render() {
    return (
      <LegendOrdinal
        direction="row"
        itemDirection="row"
        shapeMargin="0"
        labelMargin="0 0 0 4px"
        itemMargin="0 5px"
        scale={PipelineColorScale}
        shape="rect"
        fill={({ datum }: any) => PipelineColorScale(datum)}
        labelFormat={(label: string) => `${label.toUpperCase()}`}
      />
    );
  }
}
