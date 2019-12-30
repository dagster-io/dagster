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
import { SolidQueryInput } from "../SolidQueryInput";
import { filterSolidsByQuery } from "../SolidQueryImpl";

interface ISolidSelectorProps {
  pipelineName: string;
  subsetError: SubsetError;
  value: string[] | null;
  query: string | null;
  onChange: (value: string[] | null, query: string | null) => void;
  onRequestClose?: () => void;
}

interface ISolidSelectorInnerProps extends ISolidSelectorProps {
  pipeline: SolidSelectorQuery_pipeline | null;
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

  componentDidMount() {
    if (this.props.pipeline) {
      this.handleOpen(this.props);
    }
  }

  // Note: Having no elements highlighted means the entire pipeline executes.
  // The equivalent solidSubset is `null`, not `[]`, so we do some conversion here.

  handleOpen = (props: ISolidSelectorInnerProps) => {
    this.setState({ query: props.query || "*" });
  };

  handleSave = () => {
    const { query } = this.state;
    const queryResultSolids = filterSolidsByQuery(
      this.props.pipeline!.solids,
      query
    ).all;
    this.props.onChange(
      queryResultSolids.map(s => s.name),
      query
    );
  };

  render() {
    const { pipeline } = this.props;
    const { query } = this.state;

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
            backgroundColor={Colors.LIGHT_GRAY5}
            pipelineName={pipeline ? pipeline.name : ""}
            solids={pipeline ? pipeline.solids : []}
            layout={getDagrePipelineLayout(
              pipeline && pipeline.solids ? pipeline.solids : []
            )}
            focusSolids={[]}
            highlightedSolids={
              pipeline ? filterSolidsByQuery(pipeline.solids, query).all : []
            }
          />
          <div
            style={{
              position: "absolute",
              bottom: 10,
              left: "50%",
              transform: "translateX(-50%)"
            }}
          >
            <SolidQueryInput
              solids={pipeline ? pipeline.solids : []}
              value={query}
              onChange={query => this.setState({ query })}
            />
          </div>
        </div>
        <div className={Classes.DIALOG_FOOTER}>
          <div className={Classes.DIALOG_FOOTER_ACTIONS}>
            <Button onClick={this.close}>Cancel</Button>
            <Button intent="primary" onClick={this.handleSave}>
              Apply
            </Button>
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
    buttonText = "Invalid Solid Selection";
  } else {
    buttonText = query;
  }

  return (
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
        />
      </Dialog>
      <Button
        icon={subsetError ? IconNames.WARNING_SIGN : undefined}
        intent={subsetError ? Intent.WARNING : Intent.NONE}
        onClick={() => setOpen(true)}
      >
        {buttonText}
      </Button>
    </div>
  );
};
