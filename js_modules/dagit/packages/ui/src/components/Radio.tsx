import styled from 'styled-components/macro';

import {Colors} from './Colors';
import {IconWrapper} from './Icon';

export const RadioContainer = styled.div`
  .bp4-control {
    margin-bottom: 0;
    display: flex;
    flex-direction: row;
    align-items: center;
    input {
      display: none;
    }
  }

  .bp4-control.bp4-radio {
    padding: 4px 4px 4px 0;
  }

  .bp4-control.bp4-radio.bp4-disabled {
    cursor: default;
    color: ${Colors.Gray300};

    ${IconWrapper} {
      opacity: 0.3;
    }
  }

  .bp4-control .bp4-control-indicator {
    margin: 0;
    margin-right: 8px;
  }

  .bp4-control input:checked ~ .bp4-control-indicator {
    background-color: ${Colors.Blue500};
  }

  .bp4-control.bp4-radio input:disabled ~ .bp4-control-indicator {
    cursor: default;
    opacity: 0.7;
  }

  .bp4-control.bp4-radio input:disabled:checked ~ .bp4-control-indicator {
    background-color: ${Colors.Blue200};
  }

  .bp4-control .bp4-control-indicator,
  .bp4-control .bp4-control-indicator::before {
    width: 18px;
    height: 18px;
  }
`;
