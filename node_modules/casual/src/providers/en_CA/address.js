var provider = {
	provinces: ["Ontario","Quebec","Nova Scotia","New Brunswich","Manitoba","British Columbia","Prince Edward Island","Saskatchewan","Alberta","Newfoundland and Labrador","Northwest Territories","Yukon","Nunavut"],
	province_abbr: ["ON","QC","NS","NB","MB","BC","PE","SK","AB","NL","NT","YT","NU"],
	postal_code_format: ["X#X-#X#",'X#X#X#', 'X#X #X#'],
	capital_cities: ["Toronto","Quebec City","Halifax","Fredericton","Winnipeg","Victoria","Charlottetown","Regina","Edmonton","St. John's","Yellowknife","Whitehorse","Iqaluit"],

	province: function() {
		return this.random_element(this.provinces);
	},

	province_abbr: function() {
		return this.random_element(this.province_abbr);
	},

	//this isn't guaranteed to produce actually valid postal codes, as most letters unused in postal codes
	postal_code: function() {
		return this.numerify(this.letterify(this.random_element(this.postal_code_format))).toUpperCase();
	},
	//pass a province to this function to return it's capital city
	capital_city: function(prov) {
		if(prov) {
			var idx = this.provinces.indexOf(prov);
			if(idx === -1) throw new Error('province not found');
			return this.capital_cities[idx];
		}
		return this.random_element(this.capital_cities);
	}

};

module.exports = provider;