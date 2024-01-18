import {createGlobalStyle} from 'styled-components';

import {
  colorAccentRed,
  colorBackgroundBlue,
  colorBackgroundBlueHover,
  colorBackgroundCyan,
  colorBackgroundDefault,
  colorBackgroundGray,
  colorBackgroundGreen,
  colorBackgroundLight,
  colorBackgroundOlive,
  colorBackgroundRed,
  colorBackgroundYellow,
  colorBorderDefault,
  colorTextBlue,
  colorTextCyan,
  colorTextDefault,
  colorTextGreen,
  colorTextLight,
  colorTextRed,
  colorTextYellow,
} from '../theme/color';
import {Icons} from './Icon';
import {FontFamily} from './styles';

export const DagsterCodeMirrorStyle = createGlobalStyle`
  .CodeMirror-gutter-elt {
    .CodeMirror-lint-marker-error {
      background-image: none;
      background: ${colorAccentRed()};
      mask-image: url(${Icons.error});
      mask-size: cover;
      margin-bottom: 2px;
    }
  }

  .CodeMirror-cursor {
    border-color: ${colorTextLight()};
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
    background-color: ${colorBackgroundLight()};
    color: ${colorTextDefault()};

    font-family: ${FontFamily.monospace};
    font-size: 16px;

    /* Note: Theme overrides */
    &.cm-s-default .cm-comment {
      color: ${colorTextLight()};
    }

    .cm-atom {
      color: ${colorTextBlue()};
    }

    .cm-comment {
      color: ${colorTextLight()};
    }

    .cm-meta {
      color: ${colorTextLight()};
    }

    .cm-number {
      color: ${colorTextRed()};
    }

    .cm-string {
      color: ${colorTextGreen()};
    }

    .cm-string-2 {
      color: ${colorTextCyan()};
    }

    .cm-variable-2 {
      color: ${colorTextBlue()};
    }

    .cm-keyword {
      color: ${colorTextYellow()};
    }

    .CodeMirror-selected {
      background-color: ${colorBackgroundBlueHover()};
    }

    .CodeMirror-gutters {
      background-color: ${colorBackgroundDefault()};
      opacity: 0.6;
    }

    .cm-indent {
      display: inline-block;

      &.cm-zero {
        box-shadow: -1px 0 0 ${colorBackgroundGreen()};
      }

      &.cm-one {
        box-shadow: -1px 0 0 ${colorBackgroundBlue()};
      }

      &.cm-two {
        box-shadow: -1px 0 0 ${colorBackgroundCyan()};
      }

      &.cm-three {
        box-shadow: -1px 0 0 ${colorBackgroundRed()};
      }

      &.cm-four {
        box-shadow: -1px 0 0 ${colorBackgroundYellow()};
      }

      &.cm-five {
        box-shadow: -1px 0 0 ${colorBackgroundOlive()};
      }

      &.cm-six {
        box-shadow: -1px 0 0 ${colorBackgroundGray()};
      }
    }
  }

  div.CodeMirror-lint-tooltip {
    background: ${colorBackgroundDefault()};
    border: 1px solid ${colorBorderDefault()};
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
