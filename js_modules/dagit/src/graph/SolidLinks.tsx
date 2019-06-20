import * as React from "react";
import { Colors } from "@blueprintjs/core";
import { LinkVertical as Link } from "@vx/shape";
import { ILayoutConnection, IFullPipelineLayout } from "./getFullSolidLayout";
import styled from "styled-components";

export type Edge = { a: string; b: string };

export const SolidLinks = React.memo(
  (props: {
    opacity: number;
    layout: IFullPipelineLayout;
    connections: ILayoutConnection[];
    onHighlight: (arr: Edge[]) => void;
  }) => {
    const solids = props.layout.solids;

    return (
      <g style={{ opacity: props.opacity }}>
        {props.connections.map(({ from, to }, i) => (
          <g
            key={i}
            onMouseLeave={() => props.onHighlight([])}
            onMouseEnter={() =>
              props.onHighlight([{ a: from.solidName, b: to.solidName }])
            }
          >
            <StyledLink
              data={{
                // can also use from.point for the "Dagre" closest point on node
                source: solids[from.solidName].outputs[from.edgeName].port,
                target: solids[to.solidName].inputs[to.edgeName].port
              }}
            >
              <title>{`${from.solidName} - ${to.solidName}`}</title>
            </StyledLink>
          </g>
        ))}
      </g>
    );
  }
);

SolidLinks.displayName = "SolidLinks";

const StyledLink = styled(Link)`
  stroke-width: 6;
  stroke: ${Colors.BLACK}
  fill: none;
`;
