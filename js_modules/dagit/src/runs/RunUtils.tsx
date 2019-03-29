import * as React from "react";
import styled from "styled-components";
import { Colors, Spinner } from "@blueprintjs/core";

export type IRunStatus = "SUCCESS" | "NOT_STARTED" | "FAILURE" | "STARTED";

export function titleForRun(run: { runId: string }) {
  return run.runId.split("-").shift();
}

export const RunStatus: React.SFC<{ status: IRunStatus }> = ({ status }) => {
  if (status === "STARTED") {
    return <Spinner size={11} />;
  }
  return <RunStatusDot status={status} />;
};

const RunStatusDot = styled.div<{
  status: IRunStatus;
}>`
  display: inline-block;
  width: 11px;
  height: 11px;
  border-radius: 5.5px;
  align-self: center;
  transition: background 200ms linear;
  background: ${({ status }) =>
    ({
      NOT_STARTED: Colors.GRAY1,
      STARTED: Colors.GRAY3,
      SUCCESS: Colors.GREEN2,
      FAILURE: Colors.RED3
    }[status])};
  &:hover {
    background: ${({ status }) =>
      ({
        NOT_STARTED: Colors.GRAY1,
        STARTED: Colors.GRAY3,
        SUCCESS: Colors.GREEN2,
        FAILURE: Colors.RED5
      }[status])};
  }
`;
