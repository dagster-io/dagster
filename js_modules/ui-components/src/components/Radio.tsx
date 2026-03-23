// eslint-disable-next-line no-restricted-imports
import {Radio as BlueprintRadio} from '@blueprintjs/core';
import styled from 'styled-components';

import {Colors} from './Color';

// Re-export Radio from Blueprint so that we don't have to deal with the lint
// error elsewhere.
export const Radio = BlueprintRadio;

export const RadioContainer = styled.div`
  .bp5-control {
    margin-bottom: 0;
    display: flex;
    flex-direction: row;
    align-items: center;
    input {
      display: none;
    }
  }

  .bp5-control.bp5-radio {
    padding: 4px 4px 4px 0;
  }

  .bp5-control.bp5-radio.bp5-disabled {
    cursor: default;
    color: ${Colors.textDisabled()};

    .iconGlobal {
      opacity: 0.4;
    }
  }

  .bp5-control .bp5-control-indicator {
    margin: 0;
    margin-right: 8px;
  }

  .bp5-control input:checked ~ .bp5-control-indicator {
    background-color: ${Colors.accentBlue()};
  }

  .bp5-control.bp5-radio input:disabled ~ .bp5-control-indicator {
    cursor: default;
    opacity: 0.7;
    box-shadow: inset 0 0 1px ${Colors.accentPrimary()};
  }

  .bp5-control.bp5-radio input:disabled:checked ~ .bp5-control-indicator {
    background-color: ${Colors.accentBlue()};
  }

  .bp5-control .bp5-control-indicator,
  .bp5-control .bp5-control-indicator::before {
    width: 18px;
    height: 18px;
  }
`;
