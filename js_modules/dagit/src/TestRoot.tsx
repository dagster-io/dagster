import * as React from "react";
import { IRunMetadataDict } from "./RunMetadataProvider";
import { ExecutionPlanFragment } from "./plan/types/ExecutionPlanFragment";
import { RunFragment } from "./runs/types/RunFragment";
import { GaantChart } from "./GaantChart";

const Data = require("./fake-data");

interface TestRootProps {}
export class TestRoot extends React.Component<TestRootProps> {
  render() {
    return (
      <GaantChart
        metadata={Data.RunMetadata as any}
        plan={Data.ExecutionPlan as any}
        run={Data.Run as any}
      />
    );
  }
}
