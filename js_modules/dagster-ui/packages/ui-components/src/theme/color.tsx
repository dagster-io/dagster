import memoize from 'lodash/memoize';

import {getPaletteForTheme} from './theme';
import {ColorName} from '../palettes/ColorName';

const getColor = memoize((semanticName: ColorName): string => {
  const palette = getPaletteForTheme();
  return palette[semanticName];
});

export function replaceAlpha(rgbaString: string, newAlpha: number) {
  // Check if the input string is in the correct format
  const rgbaRegex = /^rgba?\((\s*\d+\s*),(\s*\d+\s*),(\s*\d+\s*),(\s*[\d.]+\s*)\)$/;
  const match = rgbaString.match(rgbaRegex);
  if (!match) {
    console.error('Invalid RGBA string format.');
    return null;
  }

  // Extract RGB values
  const red = parseInt(match[1]!.trim(), 10);
  const green = parseInt(match[2]!.trim(), 10);
  const blue = parseInt(match[3]!.trim(), 10);

  // Ensure alpha value is within the range [0, 1]
  const clampedAlpha = Math.max(0, Math.min(newAlpha, 1));

  // Construct the new RGBA string with the updated alpha value
  const newRgbaString = `rgba(${red},${green},${blue},${clampedAlpha})`;

  return newRgbaString;
}

export const browserColorScheme = () => getColor(ColorName.BrowserColorScheme);
export const colorKeylineDefault = () => getColor(ColorName.KeylineDefault);
export const colorLinkDefault = () => getColor(ColorName.LinkDefault);
export const colorLinkHover = () => getColor(ColorName.LinkHover);
export const colorLinkDisabled = () => getColor(ColorName.LinkDisabled);
export const colorTextDefault = () => getColor(ColorName.TextDefault);
export const colorTextLight = () => getColor(ColorName.TextLight);
export const colorTextLighter = () => getColor(ColorName.TextLighter);
export const colorTextDisabled = () => getColor(ColorName.TextDisabled);
export const colorTextRed = () => getColor(ColorName.TextRed);
export const colorTextYellow = () => getColor(ColorName.TextYellow);
export const colorTextGreen = () => getColor(ColorName.TextGreen);
export const colorTextBlue = () => getColor(ColorName.TextBlue);
export const colorTextOlive = () => getColor(ColorName.TextOlive);
export const colorTextCyan = () => getColor(ColorName.TextCyan);
export const colorTextLime = () => getColor(ColorName.TextLime);
export const colorBackgroundDefault = () => getColor(ColorName.BackgroundDefault);
export const colorBackgroundDefaultHover = () => getColor(ColorName.BackgroundDefaultHover);
export const colorBackgroundLight = () => getColor(ColorName.BackgroundLight);
export const colorBackgroundLightHover = () => getColor(ColorName.BackgroundLightHover);
export const colorBackgroundLighter = () => getColor(ColorName.BackgroundLighter);
export const colorBackgroundLighterHover = () => getColor(ColorName.BackgroundLighterHover);
export const colorBackgroundDisabled = () => getColor(ColorName.BackgroundDisabled);
export const colorBackgroundRed = () => getColor(ColorName.BackgroundRed);
export const colorBackgroundRedHover = () => getColor(ColorName.BackgroundRedHover);
export const colorBackgroundYellow = () => getColor(ColorName.BackgroundYellow);
export const colorBackgroundYellowHover = () => getColor(ColorName.BackgroundYellowHover);
export const colorBackgroundGreen = () => getColor(ColorName.BackgroundGreen);
export const colorBackgroundGreenHover = () => getColor(ColorName.BackgroundGreenHover);
export const colorBackgroundBlue = () => getColor(ColorName.BackgroundBlue);
export const colorBackgroundBlueHover = () => getColor(ColorName.BackgroundBlueHover);
export const colorBackgroundOlive = () => getColor(ColorName.BackgroundOlive);
export const colorBackgroundOliverHover = () => getColor(ColorName.BackgroundOliverHover);
export const colorBackgroundCyan = () => getColor(ColorName.BackgroundCyan);
export const colorBackgroundCyanHover = () => getColor(ColorName.BackgroundCyanHover);
export const colorBackgroundLime = () => getColor(ColorName.BackgroundLime);
export const colorBackgroundLimeHover = () => getColor(ColorName.BackgroundLimeHover);
export const colorBackgroundGray = () => getColor(ColorName.BackgroundGray);
export const colorBackgroundGrayHover = () => getColor(ColorName.BackgroundGrayHover);
export const colorBorderDefault = () => getColor(ColorName.BorderDefault);
export const colorBorderHover = () => getColor(ColorName.BorderHover);
export const colorBorderDisabled = () => getColor(ColorName.BorderDisabled);
export const colorFocusRing = () => getColor(ColorName.FocusRing);
export const colorAccentPrimary = () => getColor(ColorName.AccentPrimary);
export const colorAccentPrimaryHover = () => getColor(ColorName.AccentPrimaryHover);
export const colorAccentReversed = () => getColor(ColorName.AccentReversed);
export const colorAccentReversedHover = () => getColor(ColorName.AccentReversedHover);
export const colorAccentRed = () => getColor(ColorName.AccentRed);
export const colorAccentRedHover = () => getColor(ColorName.AccentRedHover);
export const colorAccentYellow = () => getColor(ColorName.AccentYellow);
export const colorAccentYellowHover = () => getColor(ColorName.AccentYellowHover);
export const colorAccentGreen = () => getColor(ColorName.AccentGreen);
export const colorAccentGreenHover = () => getColor(ColorName.AccentGreenHover);
export const colorAccentBlue = () => getColor(ColorName.AccentBlue);
export const colorAccentBlueHover = () => getColor(ColorName.AccentBlueHover);
export const colorAccentCyan = () => getColor(ColorName.AccentCyan);
export const colorAccentCyanHover = () => getColor(ColorName.AccentCyanHover);
export const colorAccentLime = () => getColor(ColorName.AccentLime);
export const colorAccentLimeHover = () => getColor(ColorName.AccentLimeHover);
export const colorAccentLavender = () => getColor(ColorName.AccentLavender);
export const colorAccentLavenderHover = () => getColor(ColorName.AccentLavenderHover);
export const colorAccentOlive = () => getColor(ColorName.AccentOlive);
export const colorAccentOliveHover = () => getColor(ColorName.AccentOliveHover);
export const colorAccentGray = () => getColor(ColorName.AccentGray);
export const colorAccentGrayHover = () => getColor(ColorName.AccentGrayHover);
export const colorAccentWhite = () => getColor(ColorName.AccentWhite);
export const colorDialogBackground = () => getColor(ColorName.DialogBackground);
export const colorTooltipBackground = () => getColor(ColorName.TooltipBackground);
export const colorTooltipText = () => getColor(ColorName.TooltipText);
export const colorPopoverBackground = () => getColor(ColorName.PopoverBackground);
export const colorPopoverBackgroundHover = () => getColor(ColorName.PopoverBackgroundHover);
export const colorShadowDefault = () => getColor(ColorName.ShadowDefault);

// NAV COLORS
export const colorNavBackground = () => getColor(ColorName.NavBackground);
export const colorNavText = () => getColor(ColorName.NavText);
export const colorNavTextHover = () => getColor(ColorName.NavTextHover);
export const colorNavTextSelected = () => getColor(ColorName.NavTextSelected);
export const colorNavButton = () => getColor(ColorName.NavButton);
export const colorNavButtonHover = () => getColor(ColorName.NavButtonHover);

// LINEAGE GRAPH COLORS
export const colorLineageDots = () => getColor(ColorName.LineageDots);
export const colorLineageEdge = () => getColor(ColorName.LineageEdge);
export const colorLineageEdgeHighlighted = () => getColor(ColorName.LineageEdgeHighlighted);

// GRAPH GROUPS
export const colorLineageGroupNodeBackground = () => getColor(ColorName.LineageGroupNodeBackground);
export const colorLineageGroupNodeBackgroundHover = () =>
  getColor(ColorName.LineageGroupNodeBackgroundHover);
export const colorLineageGroupNodeBorder = () => getColor(ColorName.LineageGroupNodeBorder);
export const colorLineageGroupNodeBorderHover = () =>
  getColor(ColorName.LineageGroupNodeBorderHover);
export const colorLineageGroupBackground = () => getColor(ColorName.LineageGroupBackground);

// GRAPH NODES
export const colorLineageNodeBackground = () => getColor(ColorName.LineageNodeBackground);
export const colorLineageNodeBackgroundHover = () => getColor(ColorName.LineageNodeBackgroundHover);
export const colorLineageNodeBorder = () => getColor(ColorName.LineageNodeBorder);
export const colorLineageNodeBorderHover = () => getColor(ColorName.LineageNodeBorderHover);
export const colorLineageNodeBorderSelected = () => getColor(ColorName.LineageNodeBorderSelected);

// Dataviz
export const colorDataVizBlue = () => getColor(ColorName.DataVizBlue);
export const colorDataVizBlueAlt = () => getColor(ColorName.DataVizBlueAlt);
export const colorDataVizBlurple = () => getColor(ColorName.DataVizBlurple);
export const colorDataVizBlurpleAlt = () => getColor(ColorName.DataVizBlurpleAlt);
export const colorDataVizBrown = () => getColor(ColorName.DataVizBrown);
export const colorDataVizBrownAlt = () => getColor(ColorName.DataVizBrownAlt);
export const colorDataVizCyan = () => getColor(ColorName.DataVizCyan);
export const colorDataVizCyanAlt = () => getColor(ColorName.DataVizCyanAlt);
export const colorDataVizGray = () => getColor(ColorName.DataVizGray);
export const colorDataVizGrayAlt = () => getColor(ColorName.DataVizGrayAlt);
export const colorDataVizGreen = () => getColor(ColorName.DataVizGreen);
export const colorDataVizGreenAlt = () => getColor(ColorName.DataVizGreenAlt);
export const colorDataVizLime = () => getColor(ColorName.DataVizLime);
export const colorDataVizLimeAlt = () => getColor(ColorName.DataVizLimeAlt);
export const colorDataVizOrange = () => getColor(ColorName.DataVizOrange);
export const colorDataVizOrangeAlt = () => getColor(ColorName.DataVizOrangeAlt);
export const colorDataVizPink = () => getColor(ColorName.DataVizPink);
export const colorDataVizPinkAlt = () => getColor(ColorName.DataVizPinkAlt);
export const colorDataVizRed = () => getColor(ColorName.DataVizRed);
export const colorDataVizRedAlt = () => getColor(ColorName.DataVizRedAlt);
export const colorDataVizTeal = () => getColor(ColorName.DataVizTeal);
export const colorDataVizTealAlt = () => getColor(ColorName.DataVizTealAlt);
export const colorDataVizViolet = () => getColor(ColorName.DataVizViolet);
export const colorDataVizVioletAlt = () => getColor(ColorName.DataVizVioletAlt);
export const colorDataVizYellow = () => getColor(ColorName.DataVizYellow);
export const colorDataVizYellowAlt = () => getColor(ColorName.DataVizYellowAlt);
