import {createGlobalStyle} from 'styled-components';

import {Colors} from './Colors';
import {Icons} from './Icon';
import {FontFamily} from './styles';

export const DagsterCodeMirrorStyle = createGlobalStyle`
  .CodeMirror-gutter-elt {
    .CodeMirror-lint-marker-error {
      background-image: none;
      background: ${Colors.Red500};
      mask-image: url(${Icons.error});
      mask-size: cover;
      margin-bottom: 2px;
    }
  }

  .CodeMirror-hint,
  .CodeMirror-lint-marker-error,
  .CodeMirror-lint-marker-warning,
  .CodeMirror-lint-message-error,
  .CodeMirror-lint-message-warning {
    font-family: ${FontFamily.monospace};
    font-size: 16px;
  }

  .CodeMirror.cm-s-dagster {
    font-family: ${FontFamily.monospace};
    font-size: 16px;

    /* Note: Theme overrides */
    &.cm-s-default .cm-comment {
      color: #999;
    }

    .cm-atom {
      color: ${Colors.Blue700};
    }

    .cm-comment {
      color: ${Colors.Gray400};
    }

    .cm-meta {
      color: ${Colors.Gray700};
    }

    .cm-number {
      color: ${Colors.Red700};
    }

    .cm-string {
      color: ${Colors.Green700};
    }

    .cm-string-2 {
      color: ${Colors.Olive700};
    }

    .cm-variable-2 {
      color: ${Colors.Blue500};
    }

    .cm-keyword {
      color: ${Colors.Yellow700};
    }

    .CodeMirror-selected {
      background-color: ${Colors.Blue50};
    }

    .CodeMirror-gutters {
      background-color: ${Colors.Gray50};
    }

    .cm-indent {
      display: inline-block;

      &.cm-zero {
        box-shadow: -1px 0 0 ${Colors.Green200};
      }

      &.cm-one {
        box-shadow: -1px 0 0 ${Colors.Blue100};
      }

      &.cm-two {
        box-shadow: -1px 0 0 ${Colors.LightPurple};
      }

      &.cm-three {
        box-shadow: -1px 0 0 ${Colors.Red200};
      }

      &.cm-four {
        box-shadow: -1px 0 0 ${Colors.Yellow200};
      }

      &.cm-five {
        box-shadow: -1px 0 0 ${Colors.Olive200};
      }

      &.cm-six {
        box-shadow: -1px 0 0 ${Colors.Gray300};
      }
    }
  }

  div.CodeMirror-lint-tooltip {
    background: rgba(255, 247, 231, 1);
    border: 1px solid ${Colors.Gray200};
  }

  .CodeMirror-lint-message {
    background: transparent;
  }
  .CodeMirror-lint-message.CodeMirror-lint-message-error {
    background: transparent;
  }

  /* Ensure that hints aren't vertically cutoff*/
  .CodeMirror-hint div {
    max-height: none !important;
  }
`;
