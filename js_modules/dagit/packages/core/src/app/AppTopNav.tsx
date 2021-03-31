import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components/macro';

import navBarImage from '../images/nav-logo-icon.png';
import navTitleImage from '../images/nav-title.png';
import {Group} from '../main';
import {VersionNumber} from '../nav/VersionNumber';
import {SearchDialog} from '../search/SearchDialog';

import {WebsocketStatus} from './WebsocketStatus';

export const AppTopNav: React.FunctionComponent<{searchPlaceholder: string}> = ({
  searchPlaceholder,
  children,
}) => {
  const history = useHistory();
  return (
    <AppTopNavContainer>
      <LogoContainer>
        <Group direction="row" spacing={16} padding={{horizontal: 12}} margin={{bottom: 8}}>
          <div style={{position: 'relative'}}>
            <img
              alt="logo"
              src={navBarImage}
              style={{height: 30}}
              onClick={() => history.push('/')}
            />
            <LogoWebsocketStatus />
          </div>
          <div>
            <img src={navTitleImage} style={{height: 10}} alt="title" />
            <VersionNumber />
          </div>
        </Group>
      </LogoContainer>
      <SearchDialog theme="dark" searchPlaceholder={searchPlaceholder} />
      {children}
    </AppTopNavContainer>
  );
};

const AppTopNavContainer = styled.div`
  background: ${Colors.DARK_GRAY2};
  display: flex;
  height: 50px;
`;

const LogoContainer = styled.div`
  cursor: pointer;
  width: 235px;
  flex-shrink: 0;
  padding-top: 10px;
  &:hover {
    img {
      filter: brightness(110%);
    }
  }
`;

const LogoWebsocketStatus = styled(WebsocketStatus)`
  position: absolute;
  top: 20px;
  left: 24px;
`;
