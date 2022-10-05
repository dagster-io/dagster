import * as React from 'react';
import styled from 'styled-components/macro';

import account_circle from '../icon-svgs/account_circle.svg';
import account_tree from '../icon-svgs/account_tree.svg';
import add from '../icon-svgs/add.svg';
import add_circle from '../icon-svgs/add_circle.svg';
import alternate_email from '../icon-svgs/alternate_email.svg';
import arrow_back from '../icon-svgs/arrow_back.svg';
import arrow_downward from '../icon-svgs/arrow_downward.svg';
import arrow_drop_down from '../icon-svgs/arrow_drop_down.svg';
import arrow_forward from '../icon-svgs/arrow_forward.svg';
import arrow_upward from '../icon-svgs/arrow_upward.svg';
import asset from '../icon-svgs/asset.svg';
import asset_group from '../icon-svgs/asset_group.svg';
import asset_non_sda from '../icon-svgs/asset_non_sda.svg';
import assignment from '../icon-svgs/assignment.svg';
import assignment_turned_in from '../icon-svgs/assignment_turned_in.svg';
import attach_file from '../icon-svgs/attach_file.svg';
import bolt from '../icon-svgs/bolt.svg';
import expectation from '../icon-svgs/bp-automatic-updates.svg';
import op from '../icon-svgs/bp-git-commit.svg';
import op_selector from '../icon-svgs/bp-send-to-graph.svg';
import cached from '../icon-svgs/cached.svg';
import cancel from '../icon-svgs/cancel.svg';
import chat_support from '../icon-svgs/chat-support.svg';
import check_circle from '../icon-svgs/check_circle.svg';
import checklist from '../icon-svgs/checklist.svg';
import chevron_left from '../icon-svgs/chevron_left.svg';
import chevron_right from '../icon-svgs/chevron_right.svg';
import close from '../icon-svgs/close.svg';
import concept_book from '../icon-svgs/concept-book.svg';
import content_copy from '../icon-svgs/content_copy.svg';
import deleteSVG from '../icon-svgs/delete.svg';
import done from '../icon-svgs/done.svg';
import download_for_offline from '../icon-svgs/download_for_offline.svg';
import drag_handle from '../icon-svgs/drag_handle.svg';
import dynamic_feed from '../icon-svgs/dynamic_feed.svg';
import edit from '../icon-svgs/edit.svg';
import email from '../icon-svgs/email.svg';
import error from '../icon-svgs/error.svg';
import error_outline from '../icon-svgs/error_outline.svg';
import expand_less from '../icon-svgs/expand_less.svg';
import expand_more from '../icon-svgs/expand_more.svg';
import filter_alt from '../icon-svgs/filter_alt.svg';
import folder from '../icon-svgs/folder.svg';
import folder_open from '../icon-svgs/folder_open.svg';
import forum from '../icon-svgs/forum.svg';
import gantt_flat from '../icon-svgs/gantt_flat.svg';
import gantt_waterfall from '../icon-svgs/gantt_waterfall.svg';
import github from '../icon-svgs/github.svg';
import github_pr_closed from '../icon-svgs/github_pr_closed.svg';
import github_pr_merged from '../icon-svgs/github_pr_merged.svg';
import github_pr_open from '../icon-svgs/github_pr_open.svg';
import graph_downstream from '../icon-svgs/graph_downstream.svg';
import graph_neighbors from '../icon-svgs/graph_neighbors.svg';
import graph_upstream from '../icon-svgs/graph_upstream.svg';
import history from '../icon-svgs/history.svg';
import history_toggle_off from '../icon-svgs/history_toggle_off.svg';
import hourglass_bottom from '../icon-svgs/hourglass_bottom.svg';
import info from '../icon-svgs/info.svg';
import job from '../icon-svgs/job.svg';
import layers from '../icon-svgs/layers.svg';
import line_style from '../icon-svgs/line_style.svg';
import linear_scale from '../icon-svgs/linear_scale.svg';
import link from '../icon-svgs/link.svg';
import list from '../icon-svgs/list.svg';
import location_on from '../icon-svgs/location_on.svg';
import lock from '../icon-svgs/lock.svg';
import logout from '../icon-svgs/logout.svg';
import materialization from '../icon-svgs/materialization.svg';
import menu from '../icon-svgs/menu.svg';
import menu_book from '../icon-svgs/menu_book.svg';
import more_horiz from '../icon-svgs/more_horiz.svg';
import nightlight from '../icon-svgs/nightlight.svg';
import noteable_logo from '../icon-svgs/noteable_logo.svg';
import observation from '../icon-svgs/observation.svg';
import open_in_new from '../icon-svgs/open_in_new.svg';
import panel_hide_right from '../icon-svgs/panel_hide_right.svg';
import panel_show_both from '../icon-svgs/panel_show_both.svg';
import panel_show_bottom from '../icon-svgs/panel_show_bottom.svg';
import panel_show_left from '../icon-svgs/panel_show_left.svg';
import panel_show_right from '../icon-svgs/panel_show_right.svg';
import panel_show_top from '../icon-svgs/panel_show_top.svg';
import people from '../icon-svgs/people.svg';
import refresh from '../icon-svgs/refresh.svg';
import replay from '../icon-svgs/replay.svg';
import schedule from '../icon-svgs/schedule.svg';
import schema from '../icon-svgs/schema.svg';
import search from '../icon-svgs/search.svg';
import sensors from '../icon-svgs/sensors.svg';
import settings from '../icon-svgs/settings.svg';
import settings_backup_restore from '../icon-svgs/settings_backup_restore.svg';
import slack from '../icon-svgs/slack.svg';
import sort_by_alpha from '../icon-svgs/sort_by_alpha.svg';
import source from '../icon-svgs/source.svg';
import speed from '../icon-svgs/speed.svg';
import splitscreen from '../icon-svgs/splitscreen.svg';
import star from '../icon-svgs/star.svg';
import subtract from '../icon-svgs/subtract.svg';
import sync_problem from '../icon-svgs/sync_problem.svg';
import table_view from '../icon-svgs/table_view.svg';
import tag from '../icon-svgs/tag.svg';
import timer from '../icon-svgs/timer.svg';
import toggle_off from '../icon-svgs/toggle_off.svg';
import toggle_on from '../icon-svgs/toggle_on.svg';
import toggle_whitespace from '../icon-svgs/toggle_whitespace.svg';
import tune from '../icon-svgs/tune.svg';
import unfold_less from '../icon-svgs/unfold_less.svg';
import unfold_more from '../icon-svgs/unfold_more.svg';
import vertical_align_bottom from '../icon-svgs/vertical_align_bottom.svg';
import vertical_align_center from '../icon-svgs/vertical_align_center.svg';
import vertical_align_top from '../icon-svgs/vertical_align_top.svg';
import view_list from '../icon-svgs/view_list.svg';
import visibility from '../icon-svgs/visibility.svg';
import visibility_off from '../icon-svgs/visibility_off.svg';
import warning from '../icon-svgs/warning.svg';
import waterfall_chart from '../icon-svgs/waterfall_chart.svg';
import workspaces from '../icon-svgs/workspaces.svg';
import wysiwyg from '../icon-svgs/wysiwyg.svg';
import youtube from '../icon-svgs/youtube.svg';
import zoom_in from '../icon-svgs/zoom_in.svg';
import zoom_out from '../icon-svgs/zoom_out.svg';

import {Colors} from './Colors';

// Mostly Material Design icons - need another one? Download the SVG:
// https://github.com/marella/material-design-icons/tree/main/svg/outlined

export const Icons = {
  // Core icons
  asset,
  asset_non_sda,
  asset_group,
  expectation,
  materialization,
  observation,
  job,
  op,
  op_selector,
  op_dynamic: bolt,
  partition_set: schedule,
  repo: source,
  resource: layers,
  run: history,
  sensors,
  schedule,
  workspace: source,
  gantt_flat,
  gantt_waterfall,

  // Other custom icons
  toggle_whitespace,
  panel_show_top,
  panel_show_left,
  panel_show_right,
  panel_hide_right,
  panel_show_bottom,
  panel_show_both,
  copy_to_clipboard: assignment,
  copy_to_clipboard_done: assignment_turned_in,
  chat_support,
  concept_book,
  open_in_new,
  folder,
  tag,
  slack,
  github,
  github_pr_open,
  github_pr_closed,
  github_pr_merged,
  youtube,

  graph_downstream,
  graph_upstream,
  graph_neighbors,

  // Material icons
  add,
  add_circle,
  account_circle,
  account_tree,
  alternate_email,
  arrow_back,
  arrow_downward,
  arrow_drop_down,
  arrow_forward,
  arrow_upward,
  assignment,
  assignment_turned_in,
  attach_file,
  bolt,
  cached,
  cancel,
  check_circle,
  checklist,
  chevron_right,
  chevron_left,
  close,
  content_copy,
  delete: deleteSVG,
  done,
  download_for_offline,
  dynamic_feed,
  drag_handle,
  edit,
  email,
  error,
  error_outline,
  expand_less,
  expand_more,
  filter_alt,
  folder_open,
  forum,
  info,
  history,
  history_toggle_off,
  hourglass_bottom,
  layers,
  line_style,
  linear_scale,
  link,
  list,
  location_on,
  lock,
  logout,
  menu,
  menu_book,
  more_horiz,
  nightlight,
  people,
  refresh,
  replay,
  schema,
  search,
  settings,
  settings_backup_restore,
  sort_by_alpha,
  source,
  subtract,
  speed,
  splitscreen,
  star,
  sync_problem,
  table_view,
  timer,
  toggle_off,
  toggle_on,
  tune,
  unfold_less,
  unfold_more,
  view_list,
  visibility,
  visibility_off,
  warning,
  workspaces,
  waterfall_chart,
  vertical_align_bottom,
  vertical_align_center,
  vertical_align_top,
  wysiwyg,
  zoom_in,
  zoom_out,

  // Integration icons
  noteable_logo,
} as const;

const SVGS_WITH_COLORS = new Set([slack]);

export type IconName = keyof typeof Icons;

const rotations: {[key in IconName]?: string} = {
  waterfall_chart: '-90deg',
};

export const IconNames = Object.keys(Icons) as IconName[];

interface Props {
  color?: string;
  name: IconName;
  size?: 16 | 20 | 24 | 48;
  style?: React.CSSProperties;
}

export const Icon = React.memo((props: Props) => {
  const {name, size = 16, style} = props;
  let img = Icons[name] || '';
  if (typeof img === 'object' && 'default' in img) {
    // in Dagit but not in Storybook due to webpack config differences
    img = (img as {default: any}).default;
  }
  let color: string | null = props.color || Colors.Dark;
  if (SVGS_WITH_COLORS.has(img)) {
    color = null;
  }
  return (
    <IconWrapper
      role="img"
      $size={size}
      $img={img}
      $color={color}
      $rotation={rotations[name] || null}
      aria-label={name}
      style={style}
    />
  );
});

interface WrapperProps {
  $color: string | null;
  $size: number;
  $img: string;
  $rotation: string | null;
}

export const IconWrapper = styled.div<WrapperProps>`
  width: ${(p) => p.$size}px;
  height: ${(p) => p.$size}px;
  flex-shrink: 0;
  flex-grow: 0;
  ${(p) =>
    p.$color === null
      ? // Increased specificity so that StyledButton background-color logic doesn't apply here.
        // We could just use !important but specificity is a little more flexible
        `
        background: url(${p.$img});
        &[role='img'][role='img'] {
          background-color: transparent;
        }
      `
      : `
        background: ${p.$color};
        mask-image: url(${p.$img});
      `}
  mask-size: cover;
  object-fit: cover;
  transition: transform 150ms linear;

  ${({$rotation}) => ($rotation ? `transform: rotate(${$rotation});` : null)}
`;
