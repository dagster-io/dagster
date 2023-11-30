import memoize from 'lodash/memoize';

import {ColorName} from '../palettes/ColorName';

import {getPaletteForTheme} from './theme';

const color = memoize((semanticName: ColorName): string => {
  const palette = getPaletteForTheme();
  return palette[semanticName];
});

export const colorKeylineDefault = () => color(ColorName.KeylineDefault);
export const colorLinkDefault = () => color(ColorName.LinkDefault);
export const colorLinkHover = () => color(ColorName.LinkHover);
export const colorLinkDisabled = () => color(ColorName.LinkDisabled);
export const colorTextDefault = () => color(ColorName.TextDefault);
export const colorTextLight = () => color(ColorName.TextLight);
export const colorTextLighter = () => color(ColorName.TextLighter);
export const colorTextDisabled = () => color(ColorName.TextDisabled);
export const colorTextRed = () => color(ColorName.TextRed);
export const colorTextYellow = () => color(ColorName.TextYellow);
export const colorTextGreen = () => color(ColorName.TextGreen);
export const colorTextBlue = () => color(ColorName.TextBlue);
export const colorTextOlive = () => color(ColorName.TextOlive);
export const colorTextCyan = () => color(ColorName.TextCyan);
export const colorTextLime = () => color(ColorName.TextLime);
export const colorBackgroundDefault = () => color(ColorName.BackgroundDefault);
export const colorBackgroundDefaultHover = () => color(ColorName.BackgroundDefaultHover);
export const colorBackgroundLight = () => color(ColorName.BackgroundLight);
export const colorBackgroundLightHover = () => color(ColorName.BackgroundLightHover);
export const colorBackgroundLighter = () => color(ColorName.BackgroundLighter);
export const colorBackgroundLighterHover = () => color(ColorName.BackgroundLighterHover);
export const colorBackgroundDisabled = () => color(ColorName.BackgroundDisabled);
export const colorBackgroundRed = () => color(ColorName.BackgroundRed);
export const colorBackgroundRedHover = () => color(ColorName.BackgroundRedHover);
export const colorBackgroundYellow = () => color(ColorName.BackgroundYellow);
export const colorBackgroundYellowHover = () => color(ColorName.BackgroundYellowHover);
export const colorBackgroundGreen = () => color(ColorName.BackgroundGreen);
export const colorBackgroundGreenHover = () => color(ColorName.BackgroundGreenHover);
export const colorBackgroundBlue = () => color(ColorName.BackgroundBlue);
export const colorBackgroundBlueHover = () => color(ColorName.BackgroundBlueHover);
export const colorBackgroundOlive = () => color(ColorName.BackgroundOlive);
export const colorBackgroundOliverHover = () => color(ColorName.BackgroundOliverHover);
export const colorBackgroundCyan = () => color(ColorName.BackgroundCyan);
export const colorBackgroundCyanHover = () => color(ColorName.BackgroundCyanHover);
export const colorBackgroundLime = () => color(ColorName.BackgroundLime);
export const colorBackgroundLimeHover = () => color(ColorName.BackgroundLimeHover);
export const colorBackgroundGray = () => color(ColorName.BackgroundGray);
export const colorBackgroundGrayHover = () => color(ColorName.BackgroundGrayHover);
export const colorBorderDefault = () => color(ColorName.BorderDefault);
export const colorBorderHover = () => color(ColorName.BorderHover);
export const colorBorderDisabled = () => color(ColorName.BorderDisabled);
export const colorFocusRing = () => color(ColorName.FocusRing);
export const colorAccentPrimary = () => color(ColorName.AccentPrimary);
export const colorAccentPrimaryHover = () => color(ColorName.AccentPrimaryHover);
export const colorAccentReversed = () => color(ColorName.AccentReversed);
export const colorAccentReversedHover = () => color(ColorName.AccentReversedHover);
export const colorAccentRed = () => color(ColorName.AccentRed);
export const colorAccentRedHover = () => color(ColorName.AccentRedHover);
export const colorAccentYellow = () => color(ColorName.AccentYellow);
export const colorAccentYellowHover = () => color(ColorName.AccentYellowHover);
export const colorAccentGreen = () => color(ColorName.AccentGreen);
export const colorAccentGreenHover = () => color(ColorName.AccentGreenHover);
export const colorAccentBlue = () => color(ColorName.AccentBlue);
export const colorAccentBlueHover = () => color(ColorName.AccentBlueHover);
export const colorAccentCyan = () => color(ColorName.AccentCyan);
export const colorAccentCyanHover = () => color(ColorName.AccentCyanHover);
export const colorAccentLime = () => color(ColorName.AccentLime);
export const colorAccentLimeHover = () => color(ColorName.AccentLimeHover);
export const colorAccentLavender = () => color(ColorName.AccentLavender);
export const colorAccentLavenderHover = () => color(ColorName.AccentLavenderHover);
export const colorAccentGray = () => color(ColorName.AccentGray);
export const colorAccentGrayHover = () => color(ColorName.AccentGrayHover);
export const colorAccentWhite = () => color(ColorName.AccentWhite);
export const colorDialogBackground = () => color(ColorName.DialogBackground);
export const colorTooltipBackground = () => color(ColorName.TooltipBackground);
export const colorTooltipText = () => color(ColorName.TooltipText);
export const colorPopoverBackground = () => color(ColorName.PopoverBackground);
export const colorPopoverBackgroundHover = () => color(ColorName.PopoverBackgroundHover);

// NAV COLORS
export const colorNavBackground = () => color(ColorName.NavBackground);
export const colorNavText = () => color(ColorName.NavText);
export const colorNavTextHover = () => color(ColorName.NavTextHover);
export const colorNavTextSelected = () => color(ColorName.NavTextSelected);
export const colorNavButton = () => color(ColorName.NavButton);
export const colorNavButtonHover = () => color(ColorName.NavButtonHover);

// LINEAGE GRAPH COLORS
export const colorLineageDots = () => color(ColorName.LineageDots);
export const colorLineageEdge = () => color(ColorName.LineageEdge);
export const colorLineageEdgeHighlighted = () => color(ColorName.LineageEdgeHighlighted);

// GRAPH GROUPS
export const colorLineageGroupNodeBackground = () => color(ColorName.LineageGroupNodeBackground);
export const colorLineageGroupNodeBackgroundHover = () =>
  color(ColorName.LineageGroupNodeBackgroundHover);
export const colorLineageGroupNodeBorder = () => color(ColorName.LineageGroupNodeBorder);
export const colorLineageGroupNodeBorderHover = () => color(ColorName.LineageGroupNodeBorderHover);
export const colorLineageGroupBackground = () => color(ColorName.LineageGroupBackground);

// GRAPH NODES
export const colorLineageNodeBackground = () => color(ColorName.LineageNodeBackground);
export const colorLineageNodeBackgroundHover = () => color(ColorName.LineageNodeBackgroundHover);
export const colorLineageNodeBorder = () => color(ColorName.LineageNodeBorder);
export const colorLineageNodeBorderHover = () => color(ColorName.LineageNodeBorderHover);
export const colorLineageNodeBorderSelected = () => color(ColorName.LineageNodeBorderSelected);

// Dataviz
export const colorDataVizBlue = () => color(ColorName.DataVizBlue);
export const colorDataVizBlueAlt = () => color(ColorName.DataVizBlueAlt);
export const colorDataVizBlurple = () => color(ColorName.DataVizBlurple);
export const colorDataVizBlurpleAlt = () => color(ColorName.DataVizBlurpleAlt);
export const colorDataVizBrown = () => color(ColorName.DataVizBrown);
export const colorDataVizBrownAlt = () => color(ColorName.DataVizBrownAlt);
export const colorDataVizCyan = () => color(ColorName.DataVizCyan);
export const colorDataVizCyanAlt = () => color(ColorName.DataVizCyanAlt);
export const colorDataVizGray = () => color(ColorName.DataVizGray);
export const colorDataVizGrayAlt = () => color(ColorName.DataVizGrayAlt);
export const colorDataVizGreen = () => color(ColorName.DataVizGreen);
export const colorDataVizGreenAlt = () => color(ColorName.DataVizGreenAlt);
export const colorDataVizLime = () => color(ColorName.DataVizLime);
export const colorDataVizLimeAlt = () => color(ColorName.DataVizLimeAlt);
export const colorDataVizOrange = () => color(ColorName.DataVizOrange);
export const colorDataVizOrangeAlt = () => color(ColorName.DataVizOrangeAlt);
export const colorDataVizPink = () => color(ColorName.DataVizPink);
export const colorDataVizPinkAlt = () => color(ColorName.DataVizPinkAlt);
export const colorDataVizRed = () => color(ColorName.DataVizRed);
export const colorDataVizRedAlt = () => color(ColorName.DataVizRedAlt);
export const colorDataVizTeal = () => color(ColorName.DataVizTeal);
export const colorDataVizTealAlt = () => color(ColorName.DataVizTealAlt);
export const colorDataVizViolet = () => color(ColorName.DataVizViolet);
export const colorDataVizVioletAlt = () => color(ColorName.DataVizVioletAlt);
export const colorDataVizYellow = () => color(ColorName.DataVizYellow);
export const colorDataVizYellowAlt = () => color(ColorName.DataVizYellowAlt);
