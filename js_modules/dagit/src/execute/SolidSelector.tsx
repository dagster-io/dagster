import {
  Colors,
  Button,
  Classes,
  Dialog,
  Intent,
  Spinner
} from "@blueprintjs/core";
import * as React from "react";
import gql from "graphql-tag";
import PipelineGraph from "../graph/PipelineGraph";
import { useQuery } from "react-apollo";
import {
  SolidSelectorQuery,
  SolidSelectorQuery_pipeline
} from "./types/SolidSelectorQuery";
import { getDagrePipelineLayout } from "../graph/getFullSolidLayout";
import { IconNames } from "@blueprintjs/icons";
import { SubsetError } from "./ExecutionSessionContainer";
import { ShortcutHandler } from "../ShortcutHandler";
import { GraphQueryInput } from "../GraphQueryInput";
import { filterByQuery, MAX_RENDERED_FOR_EMPTY_QUERY } from "../GraphQueryImpl";

interface ISolidSelectorProps {
  pipelineName: string;
  subsetError: SubsetError;
  value: string[] | null;
  query: string | null;
  onChange: (value: string[] | null, query: string | null) => void;
  onRequestClose?: () => void;
}

interface ISolidSelectorInnerProps extends ISolidSelectorProps {
  pipeline: SolidSelectorQuery_pipeline;
}

interface ISolidSelectorState {
  query: string;
}

const SolidSelectorModalContainer = (props: ISolidSelectorProps) => {
  const { data } = useQuery<SolidSelectorQuery>(SOLID_SELECTOR_QUERY, {
    variables: { name: props.pipelineName }
  });

  if (data?.pipeline?.__typename !== "Pipeline") {
    return (
      <div
        style={{
          height: `calc(100% - 85px)`,
          display: "flex",
          justifyContent: "center"
        }}
      >
        <div style={{ alignSelf: "center" }}>
          <Spinner size={32} />
        </div>
      </div>
    );
  }

  return (
    <>
      <SolidSelectorModal pipeline={data.pipeline} {...props} />
    </>
  );
};

class SolidSelectorModal extends React.PureComponent<
  ISolidSelectorInnerProps,
  ISolidSelectorState
> {
  state: ISolidSelectorState = {
    query: ""
  };

  graphRef = React.createRef<PipelineGraph>();

  componentDidMount() {
    const { query, pipeline } = this.props;

    const initialIsSlowRender =
      query === "*" && pipeline.solids.length > MAX_RENDERED_FOR_EMPTY_QUERY;
    const initial = initialIsSlowRender ? "" : query || "";

    this.handleSetQuery(initial);
  }

  handleSetQuery = (query: string) => {
    this.setState({ query }, () =>
      this.graphRef.current?.viewportEl.current?.autocenter()
    );
  };

  handleSave = () => {
    const { pipeline, onChange } = this.props;
    let { query } = this.state;

    const queryResultSolids = filterByQuery(pipeline.solids, query);
    let solidSubset: string[] | null = queryResultSolids.all.map(s => s.name);
    if (queryResultSolids.all.length === 0) {
      alert(
        "Please type a solid query that matches at least one solid " +
          "or `*` to execute the entire pipeline."
      );
      return;
    }

    // If all solids are returned, we set the subset to null rather than sending
    // a comma separated list of evey solid to the API
    if (queryResultSolids.all.length === pipeline.solids.length) {
      solidSubset = null;
      query = "*";
    }

    onChange(solidSubset, query);
  };

  render() {
    const { pipeline } = this.props;
    const { query } = this.state;

    const queryResultSolids = pipeline
      ? filterByQuery(pipeline.solids, query).all
      : [];

    const queryInvalid = queryResultSolids.length === 0 || query.length === 0;

    return (
      <>
        <div
          className={Classes.DIALOG_BODY}
          style={{
            margin: 0,
            marginBottom: 17,
            height: `calc(100% - 85px)`,
            position: "relative"
          }}
        >
          <PipelineGraph
            ref={this.graphRef}
            backgroundColor={Colors.LIGHT_GRAY5}
            pipelineName={pipeline ? pipeline.name : ""}
            solids={queryResultSolids}
            layout={getDagrePipelineLayout(queryResultSolids)}
            focusSolids={[]}
            highlightedSolids={[]}
          />
          <div
            style={{
              position: "absolute",
              bottom: 10,
              left: "50%",
              transform: "translateX(-50%)"
            }}
          >
            <GraphQueryInput
              items={pipeline ? pipeline.solids : []}
              value={query}
              placeholder="Type a Solid Subset"
              onChange={this.handleSetQuery}
              autoFocus={true}
            />
          </div>
        </div>
        <div className={Classes.DIALOG_FOOTER}>
          <div className={Classes.DIALOG_FOOTER_ACTIONS}>
            <Button onClick={this.close}>Cancel</Button>
            <ShortcutHandler
              shortcutLabel="⌥Enter"
              shortcutFilter={e => e.keyCode === 13 && e.altKey}
              onShortcut={this.handleSave}
            >
              <Button
                intent="primary"
                onClick={this.handleSave}
                disabled={queryInvalid}
                title={
                  queryInvalid
                    ? `You must provie a solid query or * to execute the entire pipeline.`
                    : `Apply solid query`
                }
              >
                Apply
              </Button>
            </ShortcutHandler>
          </div>
        </div>
      </>
    );
  }

  close = () => {
    this.props.onRequestClose && this.props.onRequestClose();
  };
}

export const SOLID_SELECTOR_QUERY = gql`
  query SolidSelectorQuery($name: String!) {
    pipeline(params: { name: $name }) {
      name
      solids {
        name
        ...PipelineGraphSolidFragment
      }
    }
  }
  ${PipelineGraph.fragments.PipelineGraphSolidFragment}
`;

export default (props: ISolidSelectorProps) => {
  const { subsetError, query } = props;
  const [open, setOpen] = React.useState(false);

  const onRequestClose = () => setOpen(false);

  let buttonText;
  if (subsetError) {
    buttonText = `Solids: Invalid Selection`;
  } else {
    buttonText = `Solids: ${query || "*"}`;
  }

  return (
    <ShortcutHandler
      shortcutLabel={"⌥S"}
      shortcutFilter={e => e.keyCode === 83 && e.altKey}
      onShortcut={() => setOpen(true)}
    >
      <div>
        <Dialog
          icon="info-sign"
          onClose={() => setOpen(false)}
          style={{ width: "80vw", maxWidth: 1400, height: "80vh" }}
          title={"Specify Solids to Execute"}
          usePortal={true}
          isOpen={open}
        >
          <SolidSelectorModalContainer
            {...props}
            onRequestClose={onRequestClose}
            onChange={(value, query) => {
              props.onChange(value, query);
              onRequestClose();
            }}
          />
        </Dialog>
        <Button
          icon={subsetError ? IconNames.ERROR : undefined}
          intent={subsetError ? Intent.WARNING : Intent.NONE}
          onClick={() => setOpen(true)}
          title="solid-subset-selector"
        >
          {buttonText}
        </Button>
      </div>
    </ShortcutHandler>
  );
};
