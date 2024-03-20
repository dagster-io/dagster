import * as React from 'react';
import styled from 'styled-components';

import {Colors} from './Color';
import account_circle from '../icon-svgs/account_circle.svg';
import account_tree from '../icon-svgs/account_tree.svg';
import add from '../icon-svgs/add.svg';
import add_circle from '../icon-svgs/add_circle.svg';
import alternate_email from '../icon-svgs/alternate_email.svg';
import arrow_back from '../icon-svgs/arrow_back.svg';
import arrow_downward from '../icon-svgs/arrow_downward.svg';
import arrow_drop_down from '../icon-svgs/arrow_drop_down.svg';
import arrow_forward from '../icon-svgs/arrow_forward.svg';
import arrow_indent from '../icon-svgs/arrow_indent.svg';
import arrow_upward from '../icon-svgs/arrow_upward.svg';
import asset from '../icon-svgs/asset.svg';
import asset_check from '../icon-svgs/asset_check.svg';
import asset_group from '../icon-svgs/asset_group.svg';
import asset_non_sda from '../icon-svgs/asset_non_sda.svg';
import asset_plot from '../icon-svgs/asset_plot.svg';
import assignment from '../icon-svgs/assignment.svg';
import assignment_turned_in from '../icon-svgs/assignment_turned_in.svg';
import attach_file from '../icon-svgs/attach_file.svg';
import auto_materialize_policy from '../icon-svgs/auto-materialize-policy.svg';
import auto_observe from '../icon-svgs/auto-observe.svg';
import backfill from '../icon-svgs/backfill.svg';
import badge from '../icon-svgs/badge.svg';
import bar_chart from '../icon-svgs/bar-chart.svg';
import bolt from '../icon-svgs/bolt.svg';
import expectation from '../icon-svgs/bp-automatic-updates.svg';
import op from '../icon-svgs/bp-git-commit.svg';
import op_selector from '../icon-svgs/bp-send-to-graph.svg';
import cached from '../icon-svgs/cached.svg';
import calendar from '../icon-svgs/calendar.svg';
import cancel from '../icon-svgs/cancel.svg';
import changes_present from '../icon-svgs/changes-present.svg';
import chat_support from '../icon-svgs/chat-support.svg';
import check_circle from '../icon-svgs/check_circle.svg';
import checklist from '../icon-svgs/checklist.svg';
import chevron_left from '../icon-svgs/chevron_left.svg';
import chevron_right from '../icon-svgs/chevron_right.svg';
import close from '../icon-svgs/close.svg';
import code_location from '../icon-svgs/code_location.svg';
import collapse_arrows from '../icon-svgs/collapse_arrows.svg';
import column_lineage from '../icon-svgs/column_lineage.svg';
import concept_book from '../icon-svgs/concept-book.svg';
import console_icon from '../icon-svgs/console.svg';
import content_copy from '../icon-svgs/content_copy.svg';
import corporate_fare from '../icon-svgs/corporate_fare.svg';
import dash from '../icon-svgs/dash.svg';
import datatype_array from '../icon-svgs/datatype_array.svg';
import datatype_bool from '../icon-svgs/datatype_bool.svg';
import datatype_number from '../icon-svgs/datatype_number.svg';
import datatype_string from '../icon-svgs/datatype_string.svg';
import date from '../icon-svgs/date.svg';
import deleteSVG from '../icon-svgs/delete.svg';
import done from '../icon-svgs/done.svg';
import dot from '../icon-svgs/dot.svg';
import dot_filled from '../icon-svgs/dot_filled.svg';
import download_for_offline from '../icon-svgs/download_for_offline.svg';
import drag_handle from '../icon-svgs/drag_handle.svg';
import dynamic_feed from '../icon-svgs/dynamic_feed.svg';
import edit from '../icon-svgs/edit.svg';
import editor_role from '../icon-svgs/editor-role.svg';
import email from '../icon-svgs/email.svg';
import error from '../icon-svgs/error.svg';
import error_outline from '../icon-svgs/error_outline.svg';
import execute from '../icon-svgs/execute.svg';
import expand from '../icon-svgs/expand.svg';
import expand_arrows from '../icon-svgs/expand_arrows.svg';
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
import gitlab from '../icon-svgs/gitlab.svg';
import graduation_cap from '../icon-svgs/graduation_cap.svg';
import graph from '../icon-svgs/graph.svg';
import graph_downstream from '../icon-svgs/graph_downstream.svg';
import graph_horizontal from '../icon-svgs/graph_horizontal.svg';
import graph_neighbors from '../icon-svgs/graph_neighbors.svg';
import graph_upstream from '../icon-svgs/graph_upstream.svg';
import graph_vertical from '../icon-svgs/graph_vertical.svg';
import history from '../icon-svgs/history.svg';
import history_toggle_off from '../icon-svgs/history_toggle_off.svg';
import hourglass from '../icon-svgs/hourglass.svg';
import hourglass_bottom from '../icon-svgs/hourglass_bottom.svg';
import id from '../icon-svgs/id.svg';
import infinity from '../icon-svgs/infinity.svg';
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
import ms_teams from '../icon-svgs/ms_teams.svg';
import multi_asset from '../icon-svgs/multi_asset.svg';
import new_in_branch from '../icon-svgs/new_in_branch.svg';
import nightlight from '../icon-svgs/nightlight.svg';
import no_access from '../icon-svgs/no_access.svg';
import notifications from '../icon-svgs/notifications.svg';
import observation from '../icon-svgs/observation.svg';
import open_in_new from '../icon-svgs/open_in_new.svg';
import panel_hide_right from '../icon-svgs/panel_hide_right.svg';
import panel_show_both from '../icon-svgs/panel_show_both.svg';
import panel_show_bottom from '../icon-svgs/panel_show_bottom.svg';
import panel_show_left from '../icon-svgs/panel_show_left.svg';
import panel_show_right from '../icon-svgs/panel_show_right.svg';
import panel_show_top from '../icon-svgs/panel_show_top.svg';
import partition from '../icon-svgs/partition.svg';
import partition_failure from '../icon-svgs/partition_failure.svg';
import partition_missing from '../icon-svgs/partition_missing.svg';
import partition_stale from '../icon-svgs/partition_stale.svg';
import partition_success from '../icon-svgs/partition_success.svg';
import password from '../icon-svgs/password.svg';
import people from '../icon-svgs/people.svg';
import refresh from '../icon-svgs/refresh.svg';
import replay from '../icon-svgs/replay.svg';
import schedule from '../icon-svgs/schedule.svg';
import schema from '../icon-svgs/schema.svg';
import search from '../icon-svgs/search.svg';
import send from '../icon-svgs/send.svg';
import sensors from '../icon-svgs/sensors.svg';
import settings from '../icon-svgs/settings.svg';
import settings_backup_restore from '../icon-svgs/settings_backup_restore.svg';
import slack from '../icon-svgs/slack.svg';
import sort_by_alpha from '../icon-svgs/sort_by_alpha.svg';
import source from '../icon-svgs/source.svg';
import source_asset from '../icon-svgs/source_asset.svg';
import speed from '../icon-svgs/speed.svg';
import splitscreen from '../icon-svgs/splitscreen.svg';
import stacks from '../icon-svgs/stacks.svg';
import star from '../icon-svgs/star.svg';
import star_outline from '../icon-svgs/star_outline.svg';
import status from '../icon-svgs/status.svg';
import sticky_note from '../icon-svgs/sticky_note.svg';
import sync_alt from '../icon-svgs/sync_alt.svg';
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
import view_column from '../icon-svgs/view_column.svg';
import view_list from '../icon-svgs/view_list.svg';
import visibility from '../icon-svgs/visibility.svg';
import visibility_off from '../icon-svgs/visibility_off.svg';
import warning from '../icon-svgs/warning.svg';
import warning_outline from '../icon-svgs/warning_outline.svg';
import waterfall_chart from '../icon-svgs/waterfall_chart.svg';
import workspaces from '../icon-svgs/workspaces.svg';
import wysiwyg from '../icon-svgs/wysiwyg.svg';
import youtube from '../icon-svgs/youtube.svg';
import zoom_in from '../icon-svgs/zoom_in.svg';
import zoom_out from '../icon-svgs/zoom_out.svg';

// Mostly Material Design icons - need another one? Download the SVG:
// https://github.com/marella/material-design-icons/tree/main/svg/outlined

export const Icons = {
  // Core icons
  auto_materialize_policy,
  auto_observe,
  asset,
  asset_check,
  asset_plot,
  asset_non_sda,
  asset_group,
  backfill,
  badge,
  date,
  datatype_array,
  datatype_bool,
  datatype_string,
  datatype_number,
  expectation,
  execute,
  materialization,
  observation,
  job,
  multi_asset,
  op,
  op_selector,
  op_dynamic: bolt,
  partition_set: schedule,
  partition,
  partition_missing,
  partition_success,
  partition_stale,
  partition_failure,
  repo: source,
  resource: layers,
  run: history,
  sensors,
  schedule,
  source_asset,
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
  calendar,
  copy_to_clipboard: assignment,
  copy_to_clipboard_done: assignment_turned_in,
  chat_support,
  changes_present,
  concept_book,
  dash,
  open_in_new,
  folder,
  tag,
  slack,
  ms_teams,
  github,
  github_pr_open,
  github_pr_closed,
  github_pr_merged,
  gitlab,
  graduation_cap,
  youtube,
  arrow_indent,
  editor_role,
  id,

  graph,
  graph_downstream,
  graph_upstream,
  graph_neighbors,
  graph_horizontal,
  graph_vertical,

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
  bar_chart,
  bolt,
  cached,
  cancel,
  check_circle,
  checklist,
  chevron_right,
  chevron_left,
  close,
  code_location,
  console: console_icon,
  content_copy,
  collapse_arrows,
  column_lineage,
  corporate_fare,
  delete: deleteSVG,
  done,
  dot,
  dot_filled,
  download_for_offline,
  dynamic_feed,
  drag_handle,
  edit,
  email,
  error,
  error_outline,
  expand,
  expand_arrows,
  expand_less,
  expand_more,
  filter_alt,
  folder_open,
  forum,
  infinity,
  info,
  history,
  history_toggle_off,
  hourglass,
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
  new_in_branch,
  nightlight,
  no_access,
  notifications,
  password,
  people,
  refresh,
  replay,
  schema,
  search,
  send,
  settings,
  settings_backup_restore,
  sort_by_alpha,
  source,
  speed,
  splitscreen,
  stacks,
  star,
  star_outline,
  status,
  sticky_note,
  sync_alt,
  sync_problem,
  table_view,
  timer,
  toggle_off,
  toggle_on,
  tune,
  unfold_less,
  unfold_more,
  view_list,
  view_column,
  visibility,
  visibility_off,
  warning,
  warning_outline,
  workspaces,
  waterfall_chart,
  vertical_align_bottom,
  vertical_align_center,
  vertical_align_top,
  wysiwyg,
  zoom_in,
  zoom_out,
} as const;

const SVGS_WITH_COLORS = new Set([(slack as any).src, (ms_teams as any).src]);

export type IconName = keyof typeof Icons;

const rotations: {[key in IconName]?: string} = {
  waterfall_chart: '-90deg',
};

export const IconNames = Object.keys(Icons) as IconName[];

interface Props {
  color?: string;
  name: IconName;
  size?: 12 | 16 | 20 | 24 | 48;
  style?: React.CSSProperties;
}

export const Icon = React.memo((props: Props) => {
  const {name, size = 16, style} = props;

  // Storybook imports SVGs are string but nextjs imports them as object.
  // This is a temporary work around until we can get storybook to import them the same way as nextjs
  const img = typeof Icons[name] === 'string' ? (Icons[name] as any) : Icons[name].src;

  const color: string | null =
    props.color || (SVGS_WITH_COLORS.has(img) ? null : Colors.accentPrimary());
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
        background-size: cover;
        &[role='img'][role='img'] {
          background-color: transparent;
        }
      `
      : `
        background: ${p.$color};
        mask-size: contain;
        mask-repeat: no-repeat;
        mask-position: center;
        mask-image: url(${p.$img});
      `}
  object-fit: contain;
  transition: transform 150ms linear;

  ${({$rotation}) => ($rotation ? `transform: rotate(${$rotation});` : null)}
`;
