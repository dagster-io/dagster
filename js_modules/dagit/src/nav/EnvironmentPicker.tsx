import React from "react";
import {
  Colors,
  Icon,
  Popover,
  Menu,
  MenuItem,
  Spinner
} from "@blueprintjs/core";
import {
  DagsterRepoOption,
  isRepositoryOptionEqual
} from "../DagsterRepositoryContext";
import styled from "styled-components/macro";
import { useHistory } from "react-router";

interface EnvironmentPickerProps {
  options: DagsterRepoOption[];
  repo: DagsterRepoOption | null;
  setRepo: (repo: DagsterRepoOption) => void;
}

export const EnvironmentPicker: React.FunctionComponent<EnvironmentPickerProps> = ({
  repo,
  setRepo,
  options
}) => {
  const history = useHistory();
  const [open, setOpen] = React.useState(false);

  const selectOption = (repo: DagsterRepoOption) => {
    setRepo(repo);
    history.push("/");
  };

  return (
    <Popover
      fill={true}
      isOpen={open}
      onInteraction={setOpen}
      minimal
      position={"bottom-left"}
      content={
        <Menu style={{ minWidth: 280 }}>
          {options.map((option, idx) => (
            <MenuItem
              key={idx}
              onClick={() => selectOption(option)}
              active={repo ? isRepositoryOptionEqual(repo, option) : false}
              icon={"git-repo"}
              text={
                <div>
                  <div>{option.repository.name}</div>
                  <div style={{ opacity: 0.5 }}>
                    {option.repositoryLocation.name}
                  </div>
                </div>
              }
            />
          ))}
        </Menu>
      }
    >
      <EnvironmentPickerFlexContainer>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 10.5, color: Colors.GRAY1 }}>ENVIRONMENT</div>
          <RepoTitle>
            {repo ? repo.repository.name : <Spinner size={16} />}
          </RepoTitle>
        </div>
        <Icon icon="caret-down" style={{ marginTop: 12, opacity: 0.9 }} />
      </EnvironmentPickerFlexContainer>
    </Popover>
  );
};

const RepoTitle = styled.div`
  overflow: hidden;
  text-overflow: ellipsis;
  opacity: 0.9;
  display: flex;
  align-items: center;
  height: 19px;
`;
const EnvironmentPickerFlexContainer = styled.div`
  border-bottom: 1px solid ${Colors.DARK_GRAY4};
  padding: 10px 10px;
  display: flex;
  align-items: center;
`;
