import styled from 'styled-components/macro';

import {Colors} from './Colors';
import {IconWrapper} from './Icon';

export const RadioContainer = styled.div`
  .bp3-control {
    margin-bottom: 0;
    display: flex;
    flex-direction: row;
    align-items: center;
    input {
      display: none;
    }
  }

  .bp3-control.bp3-radio {
    padding: 8px;
  }

  .bp3-control.bp3-radio.bp3-disabled {
    cursor: default;
    color: ${Colors.Gray300};

    ${IconWrapper} {
      opacity: 0.3;
    }
  }

  .bp3-control .bp3-control-indicator {
    margin: 0;
    margin-right: 8px;
  }

  .bp3-control input:checked ~ .bp3-control-indicator {
    background-color: ${Colors.Blue500};
  }

  .bp3-control.bp3-radio input:disabled ~ .bp3-control-indicator {
    cursor: default;
    opacity: 0.7;
  }

  .bp3-control.bp3-radio input:disabled:checked ~ .bp3-control-indicator {
    background-color: ${Colors.Blue200};
  }
`;
