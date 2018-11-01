import { Colors } from "@blueprintjs/core";
import { scaleOrdinal } from "@vx/scale";

const PipelineColorScale = scaleOrdinal({
  domain: [
    "source",
    "input",
    "solid",
    "solidDarker",
    "output",
    "materializations"
  ],
  range: [
    Colors.TURQUOISE5,
    Colors.TURQUOISE3,
    "#DBE6EE",
    "#7D8C97",
    Colors.BLUE3,
    Colors.ORANGE5
  ]
});

export default PipelineColorScale;
