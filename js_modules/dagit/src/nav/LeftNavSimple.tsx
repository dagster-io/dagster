import {Colors, Icon} from '@blueprintjs/core';
import * as React from 'react';
import {Link, LinkProps} from 'react-router-dom';
import styled from 'styled-components';

import navBarImage from 'src/images/nav-logo-icon.png';
import navTitleImage from 'src/images/nav-title.png';
import {SearchDialog} from 'src/search/SearchDialog';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';

export const LeftNavSimple = () => {
  return (
    <Box flex={{direction: 'column', justifyContent: 'space-between'}}>
      <Group direction="column" spacing={16}>
        <Group direction="column" spacing={12} padding={{top: 24, horizontal: 12}}>
          <Group direction="row" alignItems="center" spacing={8} padding={{horizontal: 4}}>
            <img alt="logo" src={navBarImage} style={{display: 'block', height: 28}} />
            <Group direction="column" spacing={2}>
              <img
                src={navTitleImage}
                style={{display: 'block', height: 10, filter: 'brightness(0.05)'}}
                alt="title"
              />
              <div style={{color: Colors.DARK_GRAY2, fontSize: '10px'}}>0.10.0</div>
            </Group>
          </Group>
          <Box padding={{right: 4}}>
            <SearchDialog />
          </Box>
        </Group>
        <div>
          <Item to="/instance/runs">
            <Icon icon="updated" iconSize={12} />
            Runs
          </Item>
          <Item to="/instance/assets">
            <Icon icon="th" iconSize={12} />
            Asset catalog
          </Item>
        </div>
        <div>
          <Item to="/workspace/pipelines" $active>
            <Icon icon="diagram-tree" iconSize={12} />
            Pipelines
          </Item>
          <Item to="/workspace/solids">
            <Icon icon="git-commit" iconSize={12} />
            Solids
          </Item>
          <Item to="/workspace/schedules">
            <Icon icon="time" iconSize={12} />
            Schedules
          </Item>
          <Item to="/workspace/sensors">
            <Icon icon="automatic-updates" iconSize={12} />
            Sensors
          </Item>
        </div>
        <div>
          <Item to="/instance">
            <Icon icon="dashboard" iconSize={12} />
            <Box
              flex={{
                grow: 1,
                justifyContent: 'space-between',
                direction: 'row',
                alignItems: 'center',
              }}
              margin={{right: 16}}
            >
              <div>Status</div>
              <div
                style={{
                  height: '10px',
                  width: '10px',
                  borderRadius: '5px',
                  backgroundColor: Colors.GREEN5,
                }}
              />
            </Box>
          </Item>
          <Item to="/settings">
            <Icon icon="cog" iconSize={12} />
            Settings
          </Item>
        </div>
      </Group>
    </Box>
  );
};

interface ItemProps extends LinkProps {
  $active?: boolean;
}

const Item = styled(Link)<ItemProps>`
  align-items: center;
  background-color: ${({$active}) => ($active ? Colors.LIGHT_GRAY4 : 'transparent')};
  color: ${({$active}) => ($active ? Colors.COBALT2 : Colors.DARK_GRAY2)};
  cursor: pointer;
  display: flex;
  flex-direction: row;
  font-weight: ${({$active}) => ($active ? 600 : 400)};
  -webkit-font-smoothing: antialiased;
  padding: 4px 0 4px 22px;

  .bp3-icon {
    display: block;
    margin-right: 8px;
  }

  .bp3-icon svg {
    fill: ${({$active}) => ($active ? Colors.COBALT2 : Colors.DARK_GRAY3)};
  }

  &:hover {
    color: ${Colors.COBALT2};
    text-decoration: none;
  }

  &:hover .bp3-icon svg {
    fill: ${Colors.COBALT2};
  }
`;
