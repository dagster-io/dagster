import { Colors } from "@blueprintjs/core";
import { scaleOrdinal } from "@vx/scale";

const PipelineColorScale = scaleOrdinal({
  domain: ["source", "input", "solid", "output", "materializations"],
  range: [
    Colors.TURQUOISE5,
    Colors.TURQUOISE3,
    "#DBE6EE",
    Colors.ORANGE3,
    Colors.ORANGE5
  ]
});

export default PipelineColorScale;
