import styled from 'styled-components/macro';

import {ColorsWIP} from '../ui/Colors';

export const OptionsContainer = styled.div`
min-height: 40px;
display: flex;
align-items: center;
padding: 5px 15px;
border-bottom: 1px solid #A7B6C2;
box-shadow: 0 1px 3px rgba(0,0,0,0.07);
background: ${ColorsWIP.White};
flex-shrink: 0;
flex-wrap: wrap;
z-index: 3;
}`;

export const OptionsDivider = styled.div`
  width: 1px;
  height: 25px;
  padding-left: 7px;
  margin-left: 7px;
  border-left: 1px solid ${ColorsWIP.Gray100};
`;

export const OptionsSpacer = styled.div`
  width: 15px;
`;
