var provider = {
	card_vendors: ['Visa', 'Visa', 'Visa', 'Visa', 'Visa', 'MasterCard', 'MasterCard', 'MasterCard', 'MasterCard', 'MasterCard', 'American Express', 'Discover Card'],

	card_params: {
		'Visa': [
			"4539############",
			"4556############",
			"4916############",
			"4532############",
			"4929############",
			"40240071########",
			"4485############",
			"4716############",
			"4###############"
		],

		'MasterCard': [
			"51##############",
			"52##############",
			"53##############",
			"54##############",
			"55##############"
		],

		'American Express': [
			"34#############",
			"37#############"
		],

		'Discover Card': [
			"6011############"
		]
	},

	card_type: function() {
		return this.random_element(this.card_vendors);
	},

	card_number: function(vendor) {
		vendor = vendor || this.card_type;
		var mask = this.random_element(this.card_params[vendor]);
		return this.numerify(mask);
	},

	card_exp: function() {
		return this.date('MM/YY');
	},

	card_data: function() {
		var type = this.card_type;
		return {
			type: type,
			number: this.card_number(type),
			exp: this.card_exp,
			holder_name: this.full_name
		};
	}
};

module.exports = provider;
