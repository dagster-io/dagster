var provider = {
  cities: ['حماه', 'الموصل', 'دمشق', 'الرباط', 'بيروت', 'الرياض', 'الكويت', 'المنامة', ''],
  
	countries: ['سوريا', 'العراق', 'اليمن', 'الجزائر', 'السعودية', 'سلطنة عمان', 'الأردن', 'النمسا', 'السويد', 'ألمانيا', 'موازمبيق', 'الكويت', 'الإمارات', 'الولايات المتحدة', 'المكسيك', 'هاواي', 'المغرب', 'تونس', 'ليبيا', 'مصر', 'فلسطين', 'الأرجنتين', 'البرازيل', 'كولومبيا', 'روسيا', 'تركيا', 'النرويج'],

	zip_formats: ['#####', '#####-####'],

	building_number_formats: ['##', '###', '####'],

	street_formats: [
		'شارع {{first_name}} {{last_name}}',
		'شارع {{last_name}}'
	],

	address1_formats: [
		'{{street}}، جانب {{address2}}',
		'{{street}}، جانب {{address2}}، بناء رقم {{building_number}}',
	],

	address2_formats: [
    'موقف {{last_name}}',
    'بقالية {{first_name}}',
    'صيدلية {{first_name}}'
  ],

	address_formats: [
		'{{city}}، {{address1}}'
	],

	country: function() {
		return this.random_element(this.countries);
	},

	city: function() {
		return this.random_element(this.cities);
	},

	zip: function(digits) {
		if (digits === 5) {
			return this.numerify(this.zip_formats[0]);
		} else if (digits === 9) {
			return this.numerify(this.zip_formats[1]);
		} else {
			return this.numerify(this.random_element(this.zip_formats));
		}
	},

	street: function() {
		return this.populate_one_of(this.street_formats);
	},

	address: function() {
		return this.populate_one_of(this.address_formats);
	},

	address1: function() {
		return this.populate_one_of(this.address1_formats);
	},

	address2: function() {
		return this.populate_one_of(this.address2_formats);
	},

	latitude: function () {
		return (this.integer(180 * 10000) / 10000.0 - 90.0).toFixed(4);
	},

	longitude: function () {
		return (this.integer(360 * 10000) / 10000.0 - 180.0).toFixed(4);
	},

	building_number: function() {
		return this.numerify(this.random_element(this.building_number_formats));
	}
};

module.exports = provider;
