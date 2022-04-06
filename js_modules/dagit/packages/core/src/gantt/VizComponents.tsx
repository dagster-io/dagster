import {Colors, CursorControlsContainer} from '@dagster-io/ui';
import styled from 'styled-components/macro';

export const OptionsContainer = styled.div`
  min-height: 56px;
  display: flex;
  align-items: center;
  padding: 5px 12px 5px 24px;
  border-bottom: 1px solid ${Colors.KeylineGray};
  background: ${Colors.White};
  flex-shrink: 0;
  flex-wrap: wrap;
  z-index: 3;

  ${CursorControlsContainer} {
    margin-top: 0;
    gap: 8px;

    @media (max-width: 1100px) {
      & .hideable-button-text {
        display: none;
      }
      & div[role='img'] {
        margin: 0;
      }
    }
  }
`;

export const OptionsDivider = styled.div`
  width: 30px;
  height: 25px;
`;

export const OptionsSpacer = styled.div`
  width: 30px;
`;
