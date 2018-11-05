import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Link } from "react-router-dom";
import { H6, Text, Code, UL } from "@blueprintjs/core";
import { pluginForMetadata } from "./plugins";

import SolidTypeSignature from "./SolidTypeSignature";
import { SolidFragment } from "./types/SolidFragment";
import TypeWithTooltip from "./TypeWithTooltip";
import {
  SidebarSection,
  SidebarTitle,
  SidebarSubhead,
  SectionItemHeader,
  SectionItemContainer
} from "./SidebarComponents";
import Description from "./Description";
import Config from "./Config";
import { SidebarSolidInfoFragment } from "./types/SidebarSolidInfoFragment";

interface ISidebarSolidInfoProps {
  solid: SolidFragment;
}

export default class SidebarSolidInfo extends React.Component<
  ISidebarSolidInfoProps,
  {}
> {
  static fragments = {
    SidebarSolidInfoFragment: gql`
      fragment SidebarSolidInfoFragment on Solid {
        ...SolidTypeSignatureFragment
        name
        definition {
          description
          metadata {
            key
            value
          }
          configDefinition {
            ...ConfigFragment
          }
        }
        inputs {
          definition {
            name
            description
            type {
              ...TypeWithTooltipFragment
            }
            expectations {
              name
              description
            }
          }
          dependsOn {
            definition {
              name
            }
            solid {
              name
            }
          }
        }
        outputs {
          definition {
            name
            description
            type {
              ...TypeWithTooltipFragment
            }
            expectations {
              name
              description
            }
            expectations {
              name
              description
            }
          }
        }
      }

      ${TypeWithTooltip.fragments.TypeWithTooltipFragment}
      ${SolidTypeSignature.fragments.SolidTypeSignatureFragment}
      ${Config.fragments.ConfigFragment}
    `
  };

  renderInputs() {
    return this.props.solid.inputs.map((input, i: number) => (
      <SectionItemContainer key={i}>
        <SectionItemHeader>{input.definition.name}</SectionItemHeader>
        <TypeWrapper>
          <TypeWithTooltip type={input.definition.type} />
        </TypeWrapper>
        <Description description={input.definition.description} />
        {input.dependsOn && (
          <Text>
            Depends on{" "}
            <Link to={`./${input.dependsOn.definition.name}`}>
              <Code>{input.dependsOn.definition.name}</Code>
            </Link>
          </Text>
        )}
        {input.definition.expectations.length > 0 ? (
          <H6>Expectations</H6>
        ) : null}
        <UL>
          {input.definition.expectations.map((expectation, i) => (
            <li key={i}>
              {expectation.name}
              <Description description={expectation.description} />
            </li>
          ))}
        </UL>
      </SectionItemContainer>
    ));
  }

  renderOutputs() {
    return this.props.solid.outputs.map((output, i: number) => (
      <SectionItemContainer key={i}>
        <SectionItemHeader>{output.definition.name}</SectionItemHeader>
        <TypeWrapper>
          <TypeWithTooltip type={output.definition.type} />
        </TypeWrapper>
        <Description description={output.definition.description} />
        {output.definition.expectations.length > 0 ? (
          <H6>Expectations</H6>
        ) : null}
        <UL>
          {output.definition.expectations.map((expectation, i) => (
            <li key={i}>
              {expectation.name}
              <Description description={expectation.description} />
            </li>
          ))}
        </UL>
      </SectionItemContainer>
    ));
  }

  public render() {
    const { solid } = this.props;

    const Plugin = pluginForMetadata(solid.definition.metadata);

    return (
      <div>
        <SidebarSubhead>Solid</SidebarSubhead>
        <SidebarTitle>{solid.name}</SidebarTitle>
        <SidebarSection title={"Type Signature"}>
          <SolidTypeSignature solid={solid} />
        </SidebarSection>
        <SidebarSection title={"Description"}>
          <Description description={solid.definition.description} />
          {Plugin &&
            Plugin.SidebarComponent && (
              <Plugin.SidebarComponent solid={solid} />
            )}
        </SidebarSection>
        {solid.definition.configDefinition && (
          <SidebarSection title={"Config"}>
            <Config config={solid.definition.configDefinition} />
          </SidebarSection>
        )}
        <SidebarSection title={"Inputs"}>{this.renderInputs()}</SidebarSection>
        <SidebarSection title={"Outputs"}>
          {this.renderOutputs()}
        </SidebarSection>
      </div>
    );
  }
}

const TypeWrapper = styled.div`
  margin-bottom: 10px;
`;

// TODO: Replace REACT_APP_GRAPHQL_URI with "DAGIT_SERVER_URI" without path
const NOTEBOOK_RENDERER_URI = process.env.REACT_APP_GRAPHQL_URI
  ? process.env.REACT_APP_GRAPHQL_URI.replace("/graphql", "/notebook")
  : "/notebook";

class PythonNotebookButton extends React.Component<{ path: string }> {
  state = {
    open: false
  };

  componentDidMount() {
    document.addEventListener("show-python-notebook", this.onClick);
  }

  componentWillUnmount() {
    document.removeEventListener("show-python-notebook", this.onClick);
  }

  onClick = () => {
    this.setState({
      open: true
    });
  };

  render() {
    return (
      <div>
        <Button icon="duplicate" onClick={this.onClick}>
          View Notebook
        </Button>
        <Dialog
          icon="info-sign"
          onClose={() =>
            this.setState({
              open: false
            })
          }
          style={{ width: "80vw", maxWidth: 900, height: 615 }}
          title={this.props.path.split("/").pop()}
          usePortal={true}
          isOpen={this.state.open}
        >
          <div className={Classes.DIALOG_BODY} style={{ margin: 0 }}>
            <iframe
              src={`${NOTEBOOK_RENDERER_URI}${this.props.path}`}
              style={{ border: 0, background: "white" }}
              seamless={true}
              width="100%"
              height={500}
            />
          </div>
          <div className={Classes.DIALOG_FOOTER}>
            <div className={Classes.DIALOG_FOOTER_ACTIONS}>
              <Button onClick={() => this.setState({ open: false })}>
                Close
              </Button>
            </div>
          </div>
        </Dialog>
      </div>
    );
  }
}
