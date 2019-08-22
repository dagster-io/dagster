import * as React from "react";
import { Colors } from "@blueprintjs/core";
import { pathVerticalDiagonal } from "@vx/shape";
import { ILayoutConnection, IFullPipelineLayout } from "./getFullSolidLayout";
import styled from "styled-components";

export type Edge = { a: string; b: string };

const buildSVGPath = pathVerticalDiagonal({
  source: (s: any) => s.source,
  target: (s: any) => s.target,
  x: (s: any) => s.x,
  y: (s: any) => s.y
});

export const SolidLinks = React.memo(
  (props: {
    opacity: number;
    layout: IFullPipelineLayout;
    connections: ILayoutConnection[];
    onHighlight: (arr: Edge[]) => void;
  }) => {
    const solids = props.layout.solids;
    const paths = props.connections.map(({ from, to }, i) =>
      buildSVGPath({
        // can also use from.point for the "Dagre" closest point on node
        source: solids[from.solidName].outputs[from.edgeName].port,
        target: solids[to.solidName].inputs[to.edgeName].port
      })
    );

    return <StyledPath d={paths.join("")} style={{ opacity: props.opacity }} />;
  }
);

SolidLinks.displayName = "SolidLinks";

const StyledPath = styled("path")`
  stroke-width: 6;
  stroke: ${Colors.BLACK}
  fill: none;
`;
