import * as React from 'react';
import styled from 'styled-components';

import {Colors} from './Color';
import account_circle from '../icon-svgs/account_circle.svg';
import account_tree from '../icon-svgs/account_tree.svg';
import add from '../icon-svgs/add.svg';
import add_circle from '../icon-svgs/add_circle.svg';
import agent from '../icon-svgs/agent.svg';
import alert from '../icon-svgs/alert.svg';
import alternate_email from '../icon-svgs/alternate_email.svg';
import approved from '../icon-svgs/approved.svg';
import arrow_back from '../icon-svgs/arrow_back.svg';
import arrow_downward from '../icon-svgs/arrow_downward.svg';
import arrow_drop_down from '../icon-svgs/arrow_drop_down.svg';
import arrow_forward from '../icon-svgs/arrow_forward.svg';
import arrow_indent from '../icon-svgs/arrow_indent.svg';
import arrow_upward from '../icon-svgs/arrow_upward.svg';
import asset from '../icon-svgs/asset.svg';
import asset_check from '../icon-svgs/asset_check.svg';
import asset_external from '../icon-svgs/asset_external.svg';
import asset_group from '../icon-svgs/asset_group.svg';
import asset_legacy from '../icon-svgs/asset_legacy.svg';
import asset_non_sda from '../icon-svgs/asset_non_sda.svg';
import asset_plot from '../icon-svgs/asset_plot.svg';
import assignment from '../icon-svgs/assignment.svg';
import assignment_turned_in from '../icon-svgs/assignment_turned_in.svg';
import attach_file from '../icon-svgs/attach_file.svg';
import auto_materialize_policy from '../icon-svgs/auto_materialize_policy.svg';
import auto_observe from '../icon-svgs/auto_observe.svg';
import automation from '../icon-svgs/automation.svg';
import backfill from '../icon-svgs/backfill.svg';
import badge from '../icon-svgs/badge.svg';
import bar_chart from '../icon-svgs/bar_chart.svg';
import base_deployment from '../icon-svgs/base_deployment.svg';
import blueprint from '../icon-svgs/blueprint.svg';
import bolt from '../icon-svgs/bolt.svg';
import branch_deployment from '../icon-svgs/branch_deployment.svg';
import bug from '../icon-svgs/bug.svg';
import cached from '../icon-svgs/cached.svg';
import calendar from '../icon-svgs/calendar.svg';
import campaign from '../icon-svgs/campaign.svg';
import cancel from '../icon-svgs/cancel.svg';
import catalog from '../icon-svgs/catalog.svg';
import changed_in_branch from '../icon-svgs/changed_in_branch.svg';
import changelog from '../icon-svgs/changelog.svg';
import changes_present from '../icon-svgs/changes_present.svg';
import chart_bar from '../icon-svgs/chart_bar.svg';
import chart_line from '../icon-svgs/chart_line.svg';
import chart_pie from '../icon-svgs/chart_pie.svg';
import chat_support from '../icon-svgs/chat_support.svg';
import check_circle from '../icon-svgs/check_circle.svg';
import check_error from '../icon-svgs/check_error.svg';
import check_failed from '../icon-svgs/check_failed.svg';
import check_filled from '../icon-svgs/check_filled.svg';
import check_missing from '../icon-svgs/check_missing.svg';
import check_passed from '../icon-svgs/check_passed.svg';
import check_started from '../icon-svgs/check_started.svg';
import check_warning from '../icon-svgs/check_warning.svg';
import checkbox_checked from '../icon-svgs/checkbox_checked.svg';
import checkbox_empty from '../icon-svgs/checkbox_empty.svg';
import checkbox_intermediate from '../icon-svgs/checkbox_intermediate.svg';
import checklist from '../icon-svgs/checklist.svg';
import chevron from '../icon-svgs/chevron.svg';
import chevron_left from '../icon-svgs/chevron_left.svg';
import chevron_right from '../icon-svgs/chevron_right.svg';
import close from '../icon-svgs/close.svg';
import cloud from '../icon-svgs/cloud.svg';
import code_block from '../icon-svgs/code_block.svg';
import code_location from '../icon-svgs/code_location.svg';
import code_location_reload from '../icon-svgs/code_location_reload.svg';
import collapse from '../icon-svgs/collapse.svg';
import collapse_arrows from '../icon-svgs/collapse_arrows.svg';
import column_lineage from '../icon-svgs/column_lineage.svg';
import column_schema from '../icon-svgs/column_schema.svg';
import compute_kind from '../icon-svgs/compute_kind.svg';
import concept_book from '../icon-svgs/concept_book.svg';
import concurrency from '../icon-svgs/concurrency.svg';
import config from '../icon-svgs/config.svg';
import console from '../icon-svgs/console.svg';
import content_copy from '../icon-svgs/content_copy.svg';
import control_flow from '../icon-svgs/control_flow.svg';
import controller from '../icon-svgs/controller.svg';
import copy from '../icon-svgs/copy.svg';
import copy_to_clipboard from '../icon-svgs/copy_to_clipboard.svg';
import copy_to_clipboard_done from '../icon-svgs/copy_to_clipboard_done.svg';
import corporate_fare from '../icon-svgs/corporate_fare.svg';
import cost_dollar from '../icon-svgs/cost_dollar.svg';
import cost_euro from '../icon-svgs/cost_euro.svg';
import cost_franc from '../icon-svgs/cost_franc.svg';
import cost_pound from '../icon-svgs/cost_pound.svg';
import cost_rupee from '../icon-svgs/cost_rupee.svg';
import cost_yen from '../icon-svgs/cost_yen.svg';
import cpu from '../icon-svgs/cpu.svg';
import create from '../icon-svgs/create.svg';
import credit_card from '../icon-svgs/credit_card.svg';
import credits from '../icon-svgs/credits.svg';
import daemon from '../icon-svgs/daemon.svg';
import dagster_primary from '../icon-svgs/dagster_primary.svg';
import dagster_reversed from '../icon-svgs/dagster_reversed.svg';
import dagster_solid from '../icon-svgs/dagster_solid.svg';
import dagsterlabs from '../icon-svgs/dagsterlabs.svg';
import dash from '../icon-svgs/dash.svg';
import data_reliability from '../icon-svgs/data_reliability.svg';
import data_type from '../icon-svgs/data_type.svg';
import database from '../icon-svgs/database.svg';
import datatype_array from '../icon-svgs/datatype_array.svg';
import datatype_bool from '../icon-svgs/datatype_bool.svg';
import datatype_number from '../icon-svgs/datatype_number.svg';
import datatype_string from '../icon-svgs/datatype_string.svg';
import date from '../icon-svgs/date.svg';
import definition from '../icon-svgs/definition.svg';
import trash from '../icon-svgs/delete.svg';
import delete_all from '../icon-svgs/delete_all.svg';
import deployment from '../icon-svgs/deployment.svg';
import description from '../icon-svgs/description.svg';
import diamond from '../icon-svgs/diamond.svg';
import dictionary from '../icon-svgs/dictionary.svg';
import documentation from '../icon-svgs/documentation.svg';
import dollar_sign from '../icon-svgs/dollar_sign.svg';
import done from '../icon-svgs/done.svg';
import dot from '../icon-svgs/dot.svg';
import dot_filled from '../icon-svgs/dot_filled.svg';
import double_check from '../icon-svgs/double_check.svg';
import download from '../icon-svgs/download.svg';
import download_for_offline from '../icon-svgs/download_for_offline.svg';
import drag_handle from '../icon-svgs/drag_handle.svg';
import duration from '../icon-svgs/duration.svg';
import dynamic_feed from '../icon-svgs/dynamic_feed.svg';
import eco from '../icon-svgs/eco.svg';
import edit from '../icon-svgs/edit.svg';
import editor_role from '../icon-svgs/editor_role.svg';
import elt from '../icon-svgs/elt.svg';
import email from '../icon-svgs/email.svg';
import error from '../icon-svgs/error.svg';
import error_outline from '../icon-svgs/error_outline.svg';
import execute from '../icon-svgs/execute.svg';
import executing from '../icon-svgs/executing.svg';
import expand from '../icon-svgs/expand.svg';
import expand_arrows from '../icon-svgs/expand_arrows.svg';
import expand_less from '../icon-svgs/expand_less.svg';
import expand_more from '../icon-svgs/expand_more.svg';
import expectation from '../icon-svgs/expectation.svg';
import file_csv from '../icon-svgs/file_csv.svg';
import file_json from '../icon-svgs/file_json.svg';
import file_markdown from '../icon-svgs/file_markdown.svg';
import file_pdf from '../icon-svgs/file_pdf.svg';
import file_sql from '../icon-svgs/file_sql.svg';
import file_yaml from '../icon-svgs/file_yaml.svg';
import filter from '../icon-svgs/filter.svg';
import filter_alt from '../icon-svgs/filter_alt.svg';
import flag from '../icon-svgs/flag.svg';
import folder from '../icon-svgs/folder.svg';
import folder_open from '../icon-svgs/folder_open.svg';
import forum from '../icon-svgs/forum.svg';
import freshness from '../icon-svgs/freshness.svg';
import gantt_flat from '../icon-svgs/gantt_flat.svg';
import gantt_time from '../icon-svgs/gantt_time.svg';
import gantt_waterfall from '../icon-svgs/gantt_waterfall.svg';
import gauge from '../icon-svgs/gauge.svg';
import git_closed from '../icon-svgs/git_closed.svg';
import git_commit from '../icon-svgs/git_commit.svg';
import git_merged from '../icon-svgs/git_merged.svg';
import git_pr from '../icon-svgs/git_pr.svg';
import git_repository from '../icon-svgs/git_repository.svg';
import github from '../icon-svgs/github.svg';
import github_pr_closed from '../icon-svgs/github_pr_closed.svg';
import github_pr_merged from '../icon-svgs/github_pr_merged.svg';
import github_pr_open from '../icon-svgs/github_pr_open.svg';
import gitlab from '../icon-svgs/gitlab.svg';
import globe from '../icon-svgs/globe.svg';
import graduation_cap from '../icon-svgs/graduation_cap.svg';
import graph from '../icon-svgs/graph.svg';
import graph_downstream from '../icon-svgs/graph_downstream.svg';
import graph_horizontal from '../icon-svgs/graph_horizontal.svg';
import graph_neighbors from '../icon-svgs/graph_neighbors.svg';
import graph_upstream from '../icon-svgs/graph_upstream.svg';
import graph_vertical from '../icon-svgs/graph_vertical.svg';
import grid from '../icon-svgs/grid.svg';
import group_by from '../icon-svgs/group_by.svg';
import heart from '../icon-svgs/heart.svg';
import help_circle from '../icon-svgs/help_circle.svg';
import history from '../icon-svgs/history.svg';
import history_toggle_off from '../icon-svgs/history_toggle_off.svg';
import hourglass from '../icon-svgs/hourglass.svg';
import hourglass_bottom from '../icon-svgs/hourglass_bottom.svg';
import hybrid from '../icon-svgs/hybrid.svg';
import id from '../icon-svgs/id.svg';
import image from '../icon-svgs/image.svg';
import infinity from '../icon-svgs/infinity.svg';
import info from '../icon-svgs/info.svg';
import info_filled from '../icon-svgs/info_filled.svg';
import ingest from '../icon-svgs/ingest.svg';
import insert from '../icon-svgs/insert.svg';
import insights from '../icon-svgs/insights.svg';
import job from '../icon-svgs/job.svg';
import key_command from '../icon-svgs/key_command.svg';
import key_option from '../icon-svgs/key_option.svg';
import key_return from '../icon-svgs/key_return.svg';
import key_shift from '../icon-svgs/key_shift.svg';
import launch from '../icon-svgs/launch.svg';
import launchpad from '../icon-svgs/launchpad.svg';
import layers from '../icon-svgs/layers.svg';
import line_style from '../icon-svgs/line_style.svg';
import lineage from '../icon-svgs/lineage.svg';
import lineage_depth from '../icon-svgs/lineage_depth.svg';
import lineage_downstream from '../icon-svgs/lineage_downstream.svg';
import lineage_horizontal from '../icon-svgs/lineage_horizontal.svg';
import lineage_upstream from '../icon-svgs/lineage_upstream.svg';
import lineage_vertical from '../icon-svgs/lineage_vertical.svg';
import linear_scale from '../icon-svgs/linear_scale.svg';
import link from '../icon-svgs/link.svg';
import list from '../icon-svgs/list.svg';
import location from '../icon-svgs/location.svg';
import location_on from '../icon-svgs/location_on.svg';
import lock from '../icon-svgs/lock.svg';
import logistics from '../icon-svgs/logistics.svg';
import logout from '../icon-svgs/logout.svg';
import logs_stderr from '../icon-svgs/logs_stderr.svg';
import logs_stdout from '../icon-svgs/logs_stdout.svg';
import logs_structured from '../icon-svgs/logs_structured.svg';
import materialization from '../icon-svgs/materialization.svg';
import materialization_event from '../icon-svgs/materialization_event.svg';
import materialization_planned from '../icon-svgs/materialization_planned.svg';
import materialization_started from '../icon-svgs/materialization_started.svg';
import memory from '../icon-svgs/memory.svg';
import menu from '../icon-svgs/menu.svg';
import menu_book from '../icon-svgs/menu_book.svg';
import metadata from '../icon-svgs/metadata.svg';
import missing from '../icon-svgs/missing.svg';
import more_horiz from '../icon-svgs/more_horiz.svg';
import more_vert from '../icon-svgs/more_vert.svg';
import ms_teams from '../icon-svgs/ms_teams.svg';
import ms_teams_color from '../icon-svgs/ms_teams_color.svg';
import multi_asset from '../icon-svgs/multi_asset.svg';
import new_svg from '../icon-svgs/new.svg';
import new_in_branch from '../icon-svgs/new_in_branch.svg';
import nightlight from '../icon-svgs/nightlight.svg';
import no_access from '../icon-svgs/no_access.svg';
import notifications from '../icon-svgs/notifications.svg';
import observation from '../icon-svgs/observation.svg';
import observation_planned from '../icon-svgs/observation_planned.svg';
import observation_started from '../icon-svgs/observation_started.svg';
import offline from '../icon-svgs/offline.svg';
import op from '../icon-svgs/op.svg';
import op_dynamic from '../icon-svgs/op_dynamic.svg';
import op_selector from '../icon-svgs/op_selector.svg';
import open_in_new from '../icon-svgs/open_in_new.svg';
import organization from '../icon-svgs/organization.svg';
import owner from '../icon-svgs/owner.svg';
import pagerduty from '../icon-svgs/pagerduty.svg';
import pagerduty_color from '../icon-svgs/pagerduty_color.svg';
import palette from '../icon-svgs/palette.svg';
import panel_hide_right from '../icon-svgs/panel_hide_right.svg';
import panel_show_both from '../icon-svgs/panel_show_both.svg';
import panel_show_bottom from '../icon-svgs/panel_show_bottom.svg';
import panel_show_left from '../icon-svgs/panel_show_left.svg';
import panel_show_right from '../icon-svgs/panel_show_right.svg';
import panel_show_top from '../icon-svgs/panel_show_top.svg';
import partition from '../icon-svgs/partition.svg';
import partition_failure from '../icon-svgs/partition_failure.svg';
import partition_missing from '../icon-svgs/partition_missing.svg';
import partition_set from '../icon-svgs/partition_set.svg';
import partition_stale from '../icon-svgs/partition_stale.svg';
import partition_success from '../icon-svgs/partition_success.svg';
import password from '../icon-svgs/password.svg';
import pause from '../icon-svgs/pause.svg';
import people from '../icon-svgs/people.svg';
import plots from '../icon-svgs/plots.svg';
import priority_1 from '../icon-svgs/priority_1.svg';
import priority_2 from '../icon-svgs/priority_2.svg';
import priority_3 from '../icon-svgs/priority_3.svg';
import priority_4 from '../icon-svgs/priority_4.svg';
import priority_5 from '../icon-svgs/priority_5.svg';
import priority_6 from '../icon-svgs/priority_6.svg';
import priority_7 from '../icon-svgs/priority_7.svg';
import priority_8 from '../icon-svgs/priority_8.svg';
import priority_9 from '../icon-svgs/priority_9.svg';
import radio_checked from '../icon-svgs/radio_checked.svg';
import radio_empty from '../icon-svgs/radio_empty.svg';
import rainbow from '../icon-svgs/rainbow.svg';
import re_execute from '../icon-svgs/re_execute.svg';
import refresh from '../icon-svgs/refresh.svg';
import reload_definitions from '../icon-svgs/reload-definitions.svg';
import reload from '../icon-svgs/reload.svg';
import replay from '../icon-svgs/replay.svg';
import repo from '../icon-svgs/repo.svg';
import reporting from '../icon-svgs/reporting.svg';
import resource from '../icon-svgs/resource.svg';
import role_admin from '../icon-svgs/role_admin.svg';
import role_custom from '../icon-svgs/role_custom.svg';
import role_editor from '../icon-svgs/role_editor.svg';
import role_launcher from '../icon-svgs/role_launcher.svg';
import role_viewer from '../icon-svgs/role_viewer.svg';
import rss from '../icon-svgs/rss.svg';
import rule from '../icon-svgs/rule.svg';
import run from '../icon-svgs/run.svg';
import run_canceled from '../icon-svgs/run_canceled.svg';
import run_failed from '../icon-svgs/run_failed.svg';
import run_queued from '../icon-svgs/run_queued.svg';
import run_started from '../icon-svgs/run_started.svg';
import run_success from '../icon-svgs/run_success.svg';
import run_with_subruns from '../icon-svgs/run_with_subruns.svg';
import schedule from '../icon-svgs/schedule.svg';
import schema from '../icon-svgs/schema.svg';
import scim_provision from '../icon-svgs/scim_provision.svg';
import search from '../icon-svgs/search.svg';
import secure from '../icon-svgs/secure.svg';
import send from '../icon-svgs/send.svg';
import sensor from '../icon-svgs/sensor.svg';
import sensors from '../icon-svgs/sensors.svg';
import serve from '../icon-svgs/serve.svg';
import serverless from '../icon-svgs/serverless.svg';
import settings from '../icon-svgs/settings.svg';
import settings_backup_restore from '../icon-svgs/settings_backup_restore.svg';
import shield from '../icon-svgs/shield.svg';
import shield_check from '../icon-svgs/shield_check.svg';
import sign_out from '../icon-svgs/sign_out.svg';
import slack from '../icon-svgs/slack.svg';
import slack_color from '../icon-svgs/slack_color.svg';
import snapshot from '../icon-svgs/snapshot.svg';
import sort_by_alpha from '../icon-svgs/sort_by_alpha.svg';
import source from '../icon-svgs/source.svg';
import source_asset from '../icon-svgs/source_asset.svg';
import speed from '../icon-svgs/speed.svg';
import splitscreen from '../icon-svgs/splitscreen.svg';
import sso from '../icon-svgs/sso.svg';
import stacks from '../icon-svgs/stacks.svg';
import star from '../icon-svgs/star.svg';
import star_double from '../icon-svgs/star_double.svg';
import star_half from '../icon-svgs/star_half.svg';
import star_outline from '../icon-svgs/star_outline.svg';
import status from '../icon-svgs/status.svg';
import step from '../icon-svgs/step.svg';
import sticky_note from '../icon-svgs/sticky_note.svg';
import storage_kind from '../icon-svgs/storage_kind.svg';
import subtract from '../icon-svgs/subtract.svg';
import success from '../icon-svgs/success.svg';
import sun from '../icon-svgs/sun.svg';
import support from '../icon-svgs/support.svg';
import sync from '../icon-svgs/sync.svg';
import sync_alt from '../icon-svgs/sync_alt.svg';
import sync_problem from '../icon-svgs/sync_problem.svg';
import table_columns from '../icon-svgs/table_columns.svg';
import table_rows from '../icon-svgs/table_rows.svg';
import table_view from '../icon-svgs/table_view.svg';
import tag from '../icon-svgs/tag.svg';
import target from '../icon-svgs/target.svg';
import team from '../icon-svgs/team.svg';
import terminate from '../icon-svgs/terminate.svg';
import test from '../icon-svgs/test.svg';
import timeline from '../icon-svgs/timeline.svg';
import timer from '../icon-svgs/timer.svg';
import timestamp from '../icon-svgs/timestamp.svg';
import toggle_off from '../icon-svgs/toggle_off.svg';
import toggle_on from '../icon-svgs/toggle_on.svg';
import toggle_whitespace from '../icon-svgs/toggle_whitespace.svg';
import token from '../icon-svgs/token.svg';
import transform from '../icon-svgs/transform.svg';
import trending_down from '../icon-svgs/trending_down.svg';
import trending_flat from '../icon-svgs/trending_flat.svg';
import trending_up from '../icon-svgs/trending_up.svg';
import tune from '../icon-svgs/tune.svg';
import unfold_less from '../icon-svgs/unfold_less.svg';
import unfold_more from '../icon-svgs/unfold_more.svg';
import university from '../icon-svgs/university.svg';
import unlocked from '../icon-svgs/unlocked.svg';
import unsynced from '../icon-svgs/unsynced.svg';
import user from '../icon-svgs/user.svg';
import variable from '../icon-svgs/variable.svg';
import verified from '../icon-svgs/verified.svg';
import vertical_align_bottom from '../icon-svgs/vertical_align_bottom.svg';
import vertical_align_center from '../icon-svgs/vertical_align_center.svg';
import vertical_align_top from '../icon-svgs/vertical_align_top.svg';
import view_column from '../icon-svgs/view_column.svg';
import view_list from '../icon-svgs/view_list.svg';
import visibility from '../icon-svgs/visibility.svg';
import visibility_off from '../icon-svgs/visibility_off.svg';
import warning from '../icon-svgs/warning.svg';
import warning_outline from '../icon-svgs/warning_outline.svg';
import water from '../icon-svgs/water.svg';
import waterfall_chart from '../icon-svgs/waterfall_chart.svg';
import webhook from '../icon-svgs/webhook.svg';
import workspace from '../icon-svgs/workspace.svg';
import workspaces from '../icon-svgs/workspaces.svg';
import wysiwyg from '../icon-svgs/wysiwyg.svg';
import x_filled from '../icon-svgs/x_filled.svg';
import youtube from '../icon-svgs/youtube.svg';
import zoom_in from '../icon-svgs/zoom_in.svg';
import zoom_out from '../icon-svgs/zoom_out.svg';

// Mostly Material Design icons - need another one? Download the SVG:
// https://github.com/marella/material-design-icons/tree/main/svg/outlined

export const Icons = {
  // Overrides
  delete: trash,
  repo,
  partition_set,
  op_dynamic,
  new: new_svg,
  //Core Icons
  account_circle,
  account_tree,
  add,
  add_circle,
  agent,
  alert,
  alternate_email,
  approved,
  arrow_back,
  arrow_downward,
  arrow_drop_down,
  arrow_forward,
  arrow_indent,
  arrow_upward,
  asset,
  asset_check,
  asset_external,
  asset_group,
  asset_legacy,
  asset_non_sda,
  asset_plot,
  assignment,
  assignment_turned_in,
  attach_file,
  auto_materialize_policy,
  auto_observe,
  automation,
  backfill,
  badge,
  bar_chart,
  base_deployment,
  blueprint,
  bolt,
  branch_deployment,
  bug,
  cached,
  calendar,
  campaign,
  cancel,
  catalog,
  changed_in_branch,
  changelog,
  changes_present,
  chart_bar,
  chart_line,
  chart_pie,
  chat_support,
  check_circle,
  check_error,
  check_failed,
  check_filled,
  check_missing,
  check_passed,
  check_started,
  check_warning,
  checkbox_checked,
  checkbox_empty,
  checkbox_intermediate,
  checklist,
  chevron,
  chevron_left,
  chevron_right,
  close,
  cloud,
  code_block,
  code_location,
  code_location_reload,
  collapse,
  collapse_arrows,
  column_lineage,
  column_schema,
  compute_kind,
  concept_book,
  concurrency,
  config,
  console,
  content_copy,
  control_flow,
  controller,
  copy,
  copy_to_clipboard,
  copy_to_clipboard_done,
  corporate_fare,
  cost_dollar,
  cost_euro,
  cost_franc,
  cost_pound,
  cost_rupee,
  cost_yen,
  cpu,
  create,
  credit_card,
  credits,
  daemon,
  dagster_primary,
  dagster_reversed,
  dagster_solid,
  dagsterlabs,
  dash,
  data_reliability,
  data_type,
  database,
  datatype_array,
  datatype_bool,
  datatype_number,
  datatype_string,
  date,
  definition,
  trash,
  delete_all,
  deployment,
  description,
  diamond,
  dictionary,
  documentation,
  dollar_sign,
  done,
  dot,
  dot_filled,
  double_check,
  download,
  download_for_offline,
  drag_handle,
  duration,
  dynamic_feed,
  eco,
  edit,
  editor_role,
  elt,
  email,
  error,
  error_outline,
  execute,
  executing,
  expand,
  expand_arrows,
  expand_less,
  expand_more,
  expectation,
  file_csv,
  file_json,
  file_markdown,
  file_pdf,
  file_sql,
  file_yaml,
  filter,
  filter_alt,
  flag,
  folder,
  folder_open,
  forum,
  freshness,
  gantt_flat,
  gantt_time,
  gantt_waterfall,
  gauge,
  git_closed,
  git_commit,
  git_merged,
  git_pr,
  git_repository,
  github,
  github_pr_closed,
  github_pr_merged,
  github_pr_open,
  gitlab,
  globe,
  graduation_cap,
  graph,
  graph_downstream,
  graph_horizontal,
  graph_neighbors,
  graph_upstream,
  graph_vertical,
  grid,
  group_by,
  heart,
  help_circle,
  history,
  history_toggle_off,
  hourglass,
  hourglass_bottom,
  hybrid,
  id,
  image,
  infinity,
  info,
  info_filled,
  ingest,
  insert,
  insights,
  job,
  key_command,
  key_option,
  key_return,
  key_shift,
  launch,
  launchpad,
  layers,
  line_style,
  lineage,
  lineage_depth,
  lineage_downstream,
  lineage_horizontal,
  lineage_upstream,
  lineage_vertical,
  linear_scale,
  link,
  list,
  location,
  location_on,
  lock,
  logistics,
  logout,
  logs_stderr,
  logs_stdout,
  logs_structured,
  materialization,
  materialization_event,
  materialization_planned,
  materialization_started,
  memory,
  menu,
  menu_book,
  metadata,
  missing,
  more_horiz,
  more_vert,
  ms_teams,
  ms_teams_color,
  multi_asset,
  new_in_branch,
  nightlight,
  no_access,
  notifications,
  observation,
  observation_planned,
  observation_started,
  offline,
  op,
  op_selector,
  open_in_new,
  organization,
  owner,
  pagerduty,
  pagerduty_color,
  palette,
  panel_hide_right,
  panel_show_both,
  panel_show_bottom,
  panel_show_left,
  panel_show_right,
  panel_show_top,
  partition,
  partition_failure,
  partition_missing,
  partition_stale,
  partition_success,
  password,
  pause,
  people,
  plots,
  priority_1,
  priority_2,
  priority_3,
  priority_4,
  priority_5,
  priority_6,
  priority_7,
  priority_8,
  priority_9,
  radio_checked,
  radio_empty,
  rainbow,
  re_execute,
  refresh,
  reload_definitions,
  reload,
  replay,
  reporting,
  resource,
  role_admin,
  role_custom,
  role_editor,
  role_launcher,
  role_viewer,
  rss,
  rule,
  run,
  run_canceled,
  run_failed,
  run_queued,
  run_started,
  run_success,
  run_with_subruns,
  schedule,
  schema,
  scim_provision,
  search,
  secure,
  send,
  sensor,
  sensors,
  serve,
  serverless,
  settings,
  settings_backup_restore,
  shield,
  shield_check,
  sign_out,
  slack,
  slack_color,
  snapshot,
  sort_by_alpha,
  source,
  source_asset,
  speed,
  splitscreen,
  sso,
  stacks,
  star,
  star_double,
  star_half,
  star_outline,
  status,
  step,
  sticky_note,
  storage_kind,
  subtract,
  success,
  sun,
  support,
  sync,
  sync_alt,
  sync_problem,
  table_columns,
  table_rows,
  table_view,
  tag,
  target,
  team,
  terminate,
  test,
  timeline,
  timer,
  timestamp,
  toggle_off,
  toggle_on,
  toggle_whitespace,
  token,
  transform,
  trending_down,
  trending_flat,
  trending_up,
  tune,
  unfold_less,
  unfold_more,
  university,
  unlocked,
  unsynced,
  user,
  variable,
  verified,
  vertical_align_bottom,
  vertical_align_center,
  vertical_align_top,
  view_column,
  view_list,
  visibility,
  visibility_off,
  warning,
  warning_outline,
  water,
  waterfall_chart,
  webhook,
  workspace,
  workspaces,
  wysiwyg,
  x_filled,
  youtube,
  zoom_in,
  zoom_out,
} as const;

export type IconName = keyof typeof Icons;

const rotations: {[key in IconName]?: string} = {
  // waterfall_chart: '-90deg',
};

export const IconNames = Object.keys(Icons) as IconName[];

interface Props {
  color?: string;
  name: IconName;
  size?: 12 | 16 | 20 | 24 | 48;
  style?: React.CSSProperties;
  useOriginalColor?: boolean;
}

export const Icon = React.memo((props: Props) => {
  const {name, size = 16, style} = props;

  // Storybook imports SVGs are string but nextjs imports them as object.
  // This is a temporary work around until we can get storybook to import them the same way as nextjs
  const img = typeof Icons[name] === 'string' ? (Icons[name] as any) : Icons[name].src;

  const color: string | null = props.useOriginalColor
    ? null
    : props.color || Colors.accentPrimary();
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
