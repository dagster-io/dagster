import {createGlobalStyle} from 'styled-components';

import {Colors} from './Color';
import {Icons} from './Icon';
import {FontFamily} from './styles';

export const DagsterCodeMirrorStyle = createGlobalStyle`
  .CodeMirror-gutter-elt {
    .CodeMirror-lint-marker-error {
      background-image: none;
      background: ${Colors.accentRed()};
      mask-image: url(${Icons.error});
      mask-size: cover;
      margin-bottom: 2px;
    }
  }

  .CodeMirror-cursor {
    border-color: ${Colors.textLight()};
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
    background-color: ${Colors.backgroundLight()};
    color: ${Colors.textDefault()};

    font-family: ${FontFamily.monospace};
    font-size: 16px;

    /* Note: Theme overrides */
    &.cm-s-default .cm-comment {
      color: ${Colors.textLight()};
    }

    .cm-atom {
      color: ${Colors.textBlue()};
    }

    .cm-comment {
      color: ${Colors.textLight()};
    }

    .cm-meta {
      color: ${Colors.textLight()};
    }

    .cm-number {
      color: ${Colors.textRed()};
    }

    .cm-string {
      color: ${Colors.textGreen()};
    }

    .cm-string-2 {
      color: ${Colors.textCyan()};
    }

    .cm-variable-2 {
      color: ${Colors.textBlue()};
    }

    .cm-keyword {
      color: ${Colors.textYellow()};
    }

    .CodeMirror-selected {
      background-color: ${Colors.backgroundBlueHover()};
    }

    .CodeMirror-gutters {
      background-color: ${Colors.backgroundDefault()};
      opacity: 0.6;
    }

    .cm-indent {
      display: inline-block;

      &.cm-zero {
        box-shadow: -1px 0 0 ${Colors.backgroundGreen()};
      }

      &.cm-one {
        box-shadow: -1px 0 0 ${Colors.backgroundBlue()};
      }

      &.cm-two {
        box-shadow: -1px 0 0 ${Colors.backgroundCyan()};
      }

      &.cm-three {
        box-shadow: -1px 0 0 ${Colors.backgroundRed()};
      }

      &.cm-four {
        box-shadow: -1px 0 0 ${Colors.backgroundYellow()};
      }

      &.cm-five {
        box-shadow: -1px 0 0 ${Colors.backgroundOlive()};
      }

      &.cm-six {
        box-shadow: -1px 0 0 ${Colors.backgroundGray()};
      }
    }
  }

  div.CodeMirror-lint-tooltip {
    background: ${Colors.backgroundDefault()};
    border: 1px solid ${Colors.borderDefault()};
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
