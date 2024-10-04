import {Box, Colors, Icon, IconWrapper, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link, NavLink} from 'react-router-dom';
import {AppTopNavRightOfLogo} from 'shared/app/AppTopNav/AppTopNavRightOfLogo.oss';
import styled from 'styled-components';

import {VersionNumber} from '../../nav/VersionNumber';
import {
  reloadFnForWorkspace,
  useRepositoryLocationReload,
} from '../../nav/useRepositoryLocationReload';
import {SearchDialog} from '../../search/SearchDialog';
import {LayoutContext} from '../LayoutProvider';
import {ShortcutHandler} from '../ShortcutHandler';
import {WebSocketStatus} from '../WebSocketProvider';

interface Props {
  children?: React.ReactNode;
  showStatusWarningIcon?: boolean;
  allowGlobalReload?: boolean;
}

export const AppTopNav = ({children, allowGlobalReload = false}: Props) => {
  const {reloading, tryReload} = useRepositoryLocationReload({
    scope: 'workspace',
    reloadFn: reloadFnForWorkspace,
  });

  return (
    <AppTopNavContainer>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
        <AppTopNavLogo />
        <AppTopNavRightOfLogo />
      </Box>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 12}} margin={{right: 20}}>
        {allowGlobalReload ? (
          <ShortcutHandler
            onShortcut={() => {
              if (!reloading) {
                tryReload();
              }
            }}
            shortcutLabel={`⌥R - ${reloading ? 'Reloading' : 'Reload all code locations'}`}
            shortcutFilter={(e) => e.altKey && e.code === 'KeyR'}
          >
            <div style={{width: '0px', height: '30px'}} />
          </ShortcutHandler>
        ) : null}
        <SearchDialog />
        {children}
      </Box>
    </AppTopNavContainer>
  );
};

export const AppTopNavLogo = () => {
  const {nav} = React.useContext(LayoutContext);
  const navButton = React.useRef<null | HTMLButtonElement>(null);

  const onToggle = React.useCallback(() => {
    navButton.current && navButton.current.focus();
    nav.isOpen ? nav.close() : nav.open();
  }, [nav]);

  const onKeyDown = React.useCallback(
    (e: React.KeyboardEvent<HTMLButtonElement>) => {
      if (e.key === 'Escape' && nav.isOpen) {
        nav.close();
      }
    },
    [nav],
  );

  return (
    <LogoContainer>
      {nav.canOpen ? (
        <ShortcutHandler
          onShortcut={() => onToggle()}
          shortcutLabel="."
          shortcutFilter={(e) => e.key === '.'}
        >
          <NavButton onClick={onToggle} onKeyDown={onKeyDown} ref={navButton}>
            <Icon name="menu" color={Colors.navTextSelected()} size={24} />
          </NavButton>
        </ShortcutHandler>
      ) : null}
      <Box flex={{display: 'inline-flex'}} margin={{left: 8}}>
        <GhostDaggyWithTooltip />
      </Box>
    </LogoContainer>
  );
};

export const GhostDaggyWithTooltip = () => {
  return (
    <DaggyTooltip
      content={
        <Box flex={{direction: 'row', gap: 4}}>
          <WebSocketStatus />
          <VersionNumber />
        </Box>
      }
      placement="bottom"
      modifiers={{offset: {enabled: true, options: {offset: [0, 18]}}}}
    >
      <Link to="/home" style={{outline: 0, display: 'flex'}}>
        <GhostDaggy />
      </Link>
    </DaggyTooltip>
  );
};

const GhostDaggy = () => (
  <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
    <g clipPath="url(#clip0_85_2786)">
      <path
        d="M12.0438 34.4556C12.0444 34.6555 12.0862 34.853 12.1666 35.0361C12.2469 35.2191 12.3641 35.3835 12.5108 35.5192C12.6576 35.6549 12.8307 35.7588 13.0193 35.8246C13.208 35.8902 13.4082 35.9163 13.6075 35.9012C21.18 35.3591 28.332 30.0001 30.6154 21.6297C30.7354 21.1483 31.0965 20.9069 31.5778 20.9069C31.8245 20.9168 32.0573 21.0236 32.2259 21.2041C32.3943 21.3846 32.485 21.6242 32.4782 21.8711C32.4782 23.7375 30.079 28.6151 26.6484 31.4457C26.4735 31.5928 26.3342 31.7775 26.2406 31.986C26.147 32.1945 26.1017 32.4215 26.1079 32.6499C26.1114 32.8357 26.1515 33.019 26.2259 33.1892C26.3004 33.3595 26.4076 33.5132 26.5417 33.642C26.6757 33.7706 26.8337 33.8715 27.0067 33.939C27.1798 34.0064 27.3645 34.039 27.5501 34.0349C27.8508 34.0349 28.332 33.8542 28.9332 33.3121C31.3322 31.1436 35.9045 25.0617 35.9045 18.377C35.9045 8.57653 28.3277 0.131348 17.7536 0.131348C8.31825 0.131348 0.144531 7.83958 0.144531 16.7521C0.144531 22.6532 4.83256 27.1088 11.0221 27.1088C15.7708 27.1088 20.1583 23.7375 21.3607 19.0998C21.4805 18.6184 21.8404 18.377 22.3217 18.377C22.5684 18.3869 22.8015 18.4936 22.9702 18.6742C23.1389 18.8546 23.23 19.0942 23.2235 19.3412C23.2235 21.449 19.2566 28.8001 11.2028 28.8001C9.27928 28.8001 6.87599 28.2579 5.19242 27.2937C4.96705 27.1844 4.72154 27.1229 4.47129 27.113C4.27969 27.1057 4.08862 27.138 3.91011 27.2082C3.73161 27.2782 3.56954 27.3845 3.43408 27.5202C3.29862 27.656 3.19271 27.8183 3.123 27.9971C3.0533 28.1758 3.02131 28.3669 3.02905 28.5587C3.03683 28.8042 3.10715 29.0437 3.23334 29.2544C3.35954 29.4651 3.53742 29.6402 3.75016 29.7629C5.97423 31.0335 8.61883 31.6899 11.3227 31.6899C18.0542 31.6899 24.1845 27.113 25.988 20.369C26.1079 19.8876 26.4691 19.6462 26.949 19.6462C27.1958 19.6561 27.4289 19.7628 27.5976 19.9432C27.7663 20.1238 27.8573 20.3634 27.8508 20.6104C27.8508 23.3803 22.9228 32.2928 13.4268 33.0156C13.0594 33.0428 12.715 33.2049 12.4598 33.4707C12.2045 33.7364 12.0564 34.0873 12.0438 34.4556Z"
        fill="#DEDEFC"
      />
      <path
        d="M21.4537 11.3929C22.7498 11.3832 24.0221 11.7416 25.1229 12.4263C25.2341 11.8173 25.2955 11.2002 25.3064 10.5811C25.3064 7.72232 23.1275 5.16138 20.4743 5.16138C18.4112 5.16138 17.1213 6.87102 17.1213 8.98302C17.1115 10.124 17.5122 11.2304 18.2503 12.1002C19.2502 11.6232 20.346 11.3813 21.4537 11.3929Z"
        fill="white"
      />
      <path
        d="M27.6704 21.7497C28.0387 20.4904 28.201 19.6165 28.201 19.049C28.1897 18.8039 28.0847 18.5725 27.9077 18.4027C27.7306 18.233 27.4952 18.1378 27.2498 18.137C27.0214 18.1412 26.8008 18.2218 26.6234 18.3658C26.4459 18.5098 26.3217 18.709 26.2704 18.9318C26.1702 19.3454 25.9558 20.4664 25.7441 21.1779C25.8315 20.9115 25.9116 20.641 25.984 20.3661C26.104 19.8833 26.4651 19.6433 26.945 19.6433C27.1916 19.6529 27.4247 19.7594 27.5934 19.9395C27.7623 20.1198 27.8533 20.3592 27.8468 20.6061C27.8354 20.9942 27.7733 21.3792 27.6619 21.7511L27.6704 21.7497Z"
        fill="#C9C6FA"
      />
      <path
        d="M32.7789 20.434C32.7674 20.1893 32.6625 19.9582 32.4857 19.7887C32.3091 19.619 32.0741 19.5235 31.8291 19.522C31.601 19.5265 31.3807 19.6072 31.2036 19.7512C31.0264 19.8952 30.9024 20.0943 30.8512 20.3168C30.7495 20.7403 30.5309 21.8782 30.3164 22.5883H30.3263C30.4306 22.2721 30.528 21.9516 30.6085 21.6255C30.7284 21.1427 31.0896 20.9027 31.5709 20.9027C31.8175 20.9123 32.0503 21.0187 32.2189 21.199C32.3875 21.3793 32.4781 21.6187 32.4713 21.8655C32.4644 22.1652 32.4232 22.4631 32.3485 22.7535C32.6477 21.7031 32.7789 20.9436 32.7789 20.434Z"
        fill="#C9C6FA"
      />
      <path
        d="M21.454 11.393C22.0981 11.3917 22.7395 11.4777 23.3605 11.6486C23.6867 11.2037 23.8496 10.6601 23.8219 10.1092C23.7944 9.55826 23.5778 9.03366 23.2089 8.62367C22.84 8.21369 22.3413 7.94335 21.7965 7.85815C21.2517 7.77295 20.6941 7.87809 20.2178 8.15588L21.2056 9.78223L19.3555 8.98176C19.1049 9.38627 18.9793 9.85581 18.9944 10.3315C19.0095 10.8072 19.1645 11.2678 19.4402 11.6556C20.0968 11.4786 20.7741 11.3903 21.454 11.393Z"
        fill="#030615"
      />
      <path
        d="M7.20026 21.8597C7.97966 21.8597 8.61148 21.2276 8.61148 20.4479C8.61148 19.6682 7.97966 19.0361 7.20026 19.0361C6.42087 19.0361 5.78906 19.6682 5.78906 20.4479C5.78906 21.2276 6.42087 21.8597 7.20026 21.8597Z"
        fill="#C9C6FA"
      />
      <path
        d="M7.20026 16.2127C7.97966 16.2127 8.61148 15.5807 8.61148 14.801C8.61148 14.0212 7.97966 13.3892 7.20026 13.3892C6.42087 13.3892 5.78906 14.0212 5.78906 14.801C5.78906 15.5807 6.42087 16.2127 7.20026 16.2127Z"
        fill="#C9C6FA"
      />
      <path
        d="M4.378 19.0362C5.15739 19.0362 5.78921 18.4041 5.78921 17.6244C5.78921 16.8447 5.15739 16.2126 4.378 16.2126C3.59862 16.2126 2.9668 16.8447 2.9668 17.6244C2.9668 18.4041 3.59862 19.0362 4.378 19.0362Z"
        fill="#C9C6FA"
      />
      <path
        d="M10.729 27.1059H11.0113C15.7599 27.1059 20.1474 23.7346 21.3498 19.0969C21.4697 18.6155 21.8295 18.3741 22.3108 18.3741C22.5576 18.384 22.7907 18.4907 22.9594 18.6713C23.1281 18.8517 23.2191 19.0913 23.2126 19.3383C23.191 19.831 23.0797 20.3158 22.8837 20.7684C22.9179 20.7159 22.9475 20.6606 22.9726 20.6033C23.3297 19.7868 23.5142 18.9053 23.5146 18.0141C23.5146 16.6291 22.5521 15.7256 21.1705 15.7256C18.7616 15.7256 18.2789 17.8291 17.2629 20.0781C16.2087 22.4131 14.2726 24.9388 9.3898 24.9388C4.31651 24.9388 -0.896499 21.3854 0.375 14.16C0.390523 14.0696 0.403223 13.9891 0.413101 13.9143C0.226792 14.8478 0.132261 15.7972 0.130859 16.7491C0.144972 22.5656 4.68765 26.9703 10.729 27.1059Z"
        fill="#C9C6FA"
      />
    </g>
    <defs>
      <clipPath id="clip0_85_2786">
        <rect width="36" height="36" fill="white" />
      </clipPath>
    </defs>
  </svg>
);

const DaggyTooltip = styled(Tooltip)`
  &.bp5-popover-target {
    display: inline-flex;
  }
`;

export const TopNavLink = styled(NavLink)`
  color: ${Colors.navText()};
  font-weight: 600;
  transition: color 50ms linear;
  padding: 24px 0;
  text-decoration: none;

  :hover {
    color: ${Colors.navTextHover()};
    text-decoration: none;
  }

  :active,
  &.active {
    color: ${Colors.navTextSelected()};
    text-decoration: none;
  }

  :focus {
    outline: none !important;
    color: ${Colors.navTextSelected()};
  }
`;

export const AppTopNavContainer = styled.div`
  background: ${Colors.navBackground()};
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  height: 64px;
`;

const LogoContainer = styled.div`
  cursor: pointer;
  display: flex;
  align-items: center;
  flex-shrink: 0;
  padding-left: 12px;

  svg {
    transition: filter 100ms;
  }

  &:hover {
    svg {
      filter: brightness(90%);
    }
  }
`;

const NavButton = styled.button`
  border-radius: 20px;
  cursor: pointer;
  margin-left: 4px;
  outline: none;
  padding: 6px;
  border: none;
  background: ${Colors.navBackground()};
  display: block;

  ${IconWrapper} {
    transition: background 100ms linear;
  }

  :hover ${IconWrapper} {
    background: ${Colors.navTextHover()};
  }

  :active ${IconWrapper} {
    background: ${Colors.navTextHover()};
  }

  :focus {
    background: ${Colors.navButton()};
  }
`;
