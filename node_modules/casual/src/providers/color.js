var provider = {

	safe_color_names: [
		'black', 'maroon', 'green', 'navy', 'olive',
		'purple', 'teal', 'lime', 'blue', 'silver',
		'gray', 'yellow', 'fuchsia', 'aqua', 'white'
	],

	color_names: [
		'AliceBlue', 'AntiqueWhite', 'Aqua', 'Aquamarine',
		'Azure', 'Beige', 'Bisque', 'Black', 'BlanchedAlmond',
		'Blue', 'BlueViolet', 'Brown', 'BurlyWood', 'CadetBlue',
		'Chartreuse', 'Chocolate', 'Coral', 'CornflowerBlue',
		'Cornsilk', 'Crimson', 'Cyan', 'DarkBlue', 'DarkCyan',
		'DarkGoldenRod', 'DarkGray', 'DarkGreen', 'DarkKhaki',
		'DarkMagenta', 'DarkOliveGreen', 'Darkorange', 'DarkOrchid',
		'DarkRed', 'DarkSalmon', 'DarkSeaGreen', 'DarkSlateBlue',
		'DarkSlateGray', 'DarkTurquoise', 'DarkViolet', 'DeepPink',
		'DeepSkyBlue', 'DimGray', 'DimGrey', 'DodgerBlue', 'FireBrick',
		'FloralWhite', 'ForestGreen', 'Fuchsia', 'Gainsboro', 'GhostWhite',
		'Gold', 'GoldenRod', 'Gray', 'Green', 'GreenYellow', 'HoneyDew',
		'HotPink', 'IndianRed ', 'Indigo ', 'Ivory', 'Khaki', 'Lavender',
		'LavenderBlush', 'LawnGreen', 'LemonChiffon', 'LightBlue', 'LightCoral',
		'LightCyan', 'LightGoldenRodYellow', 'LightGray', 'LightGreen', 'LightPink',
		'LightSalmon', 'LightSeaGreen', 'LightSkyBlue', 'LightSlateGray', 'LightSteelBlue',
		'LightYellow', 'Lime', 'LimeGreen', 'Linen', 'Magenta', 'Maroon', 'MediumAquaMarine',
		'MediumBlue', 'MediumOrchid', 'MediumPurple', 'MediumSeaGreen', 'MediumSlateBlue',
		'MediumSpringGreen', 'MediumTurquoise', 'MediumVioletRed', 'MidnightBlue',
		'MintCream', 'MistyRose', 'Moccasin', 'NavajoWhite', 'Navy', 'OldLace', 'Olive',
		'OliveDrab', 'Orange', 'OrangeRed', 'Orchid', 'PaleGoldenRod', 'PaleGreen',
		'PaleTurquoise', 'PaleVioletRed', 'PapayaWhip', 'PeachPuff', 'Peru', 'Pink', 'Plum',
		'PowderBlue', 'Purple', 'Red', 'RosyBrown', 'RoyalBlue', 'SaddleBrown', 'Salmon',
		'SandyBrown', 'SeaGreen', 'SeaShell', 'Sienna', 'Silver', 'SkyBlue', 'SlateBlue',
		'SlateGray', 'Snow', 'SpringGreen', 'SteelBlue', 'Tan', 'Teal', 'Thistle', 'Tomato',
		'Turquoise', 'Violet', 'Wheat', 'White', 'WhiteSmoke', 'Yellow', 'YellowGreen'
	],

	color_name: function() {
		return this.random_element(this.color_names);
	},

	safe_color_name: function() {
		return this.random_element(this.safe_color_names);
	},

	rgb_hex: function() {
		return '#' + ('000000' + this.integer(0, 16777216).toString(16)).slice(-6);
	},

	rgb_array: function() {
		return [this.integer(0, 255), this.integer(0, 255), this.integer(0, 255)];
	}
};

module.exports = provider;
