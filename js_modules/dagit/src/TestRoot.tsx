import * as React from "react";
import { GaantChart } from "./GaantChart";

// eslint-disable-next-line @typescript-eslint/no-var-requires
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
