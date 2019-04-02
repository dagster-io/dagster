import * as React from "react";
import { PipelineRunStatus } from "../types/globalTypes";

const link = (document.querySelector("link[rel*='icon']") ||
  document.createElement("link")) as HTMLLinkElement;
link.type = "image/x-icon";
link.rel = "shortcut icon";
document.getElementsByTagName("head")[0].appendChild(link);

const title = document.querySelector("title") as HTMLTitleElement;

const FaviconsForStatus = {
  [PipelineRunStatus.FAILURE]: "/favicon_failed.ico",
  [PipelineRunStatus.STARTED]: "/favicon_pending.ico",
  [PipelineRunStatus.NOT_STARTED]: "/favicon_pending.ico",
  [PipelineRunStatus.SUCCESS]: "/favicon_success.ico"
};

export class PipelineStatusToPageAttributes extends React.Component<{
  pipelineName: string;
  runId: string;
  status: PipelineRunStatus;
}> {
  componentDidMount() {
    this.updatePageAttributes();
  }

  componentDidUpdate() {
    this.updatePageAttributes();
  }

  componentWillUnmount() {
    link.href = "/favicon.ico";
    title.textContent = "Dagit";
  }

  updatePageAttributes() {
    const { status, pipelineName, runId } = this.props;

    title.textContent = `${pipelineName} ${runId} [${status}]`;
    link.href = FaviconsForStatus[this.props.status] || "/favicon.ico";
  }

  render() {
    return <span />;
  }
}
