var provider = {
	
	safe_color_names: [
		'أسود', 'أحمر', 'أخضر', 'نيلي', 'زيتوني',
		'بنفسجي', 'زيتي', 'ليموني', 'أزرق', 'فضي',
		'رمادي', 'أصفر', 'فوشي', 'تركواز', 'أبيض'
	],

	color_names: [
		'أسود', 'أحمر', 'أخضر', 'نيلي', 'زيتوني',
		'بنفسجي', 'زيتي', 'ليموني', 'أزرق', 'فضي',
		'رمادي', 'أصفر', 'فوشي', 'تركواز', 'أبيض'
	],

	color_name: function() {
		return this.random_element(this.color_names);
	},

	safe_color_name: function() {
		return this.random_element(this.safe_color_names);
	},

	rgb_hex: function() {
		return '#' + this.integer(0, 16777216).toString(16);
	},

	rgb_array: function() {
		return [this.integer(0, 255), this.integer(0, 255), this.integer(0, 255)];
	}
};

module.exports = provider;
