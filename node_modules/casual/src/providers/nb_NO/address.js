var provider = {

	countries: [
		'Abkhasia', 'Afghanistan', 'Albania', 'Algerie', 'Andorra', 'Angola', 'Antigua og Barbuda', 'Argentina', 'Armenia', 'Aserbajdsjan', 'Australia',
		'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados', 'Belgia', 'Belize', 'Benin', 'Bhutan', 'Bolivia', 'Bosnia-Hercegovina', 'Botswana', 'Brasil', 'Brunei', 'Bulgaria', 'Burkina Faso', 'Burundi',
		'Canada', 'Chile', 'Colombia', 'Costa Rica', 'Cuba',
		'Danmark', 'De forente arabiske emirater', 'Den demokratiske republikken Kongo', 'Den dominikanske republikk', 'Den sentralafrikanske republikk', 'Djibouti', 'Dominica',
		'Ecuador', 'Egypt', 'Ekvatorial-Guinea', 'Elfenbenskysten', 'El Salvador', 'Eritrea', 'Estland', 'Etiopia',
		'Fiji', 'Filippinene', 'Finland', 'Frankrike',
		'Gabon', 'Gambia', 'Georgia', 'Ghana', 'Grenada', 'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana',
		'Haiti', 'Hellas', 'Honduras', 'Hviterussland',
		'India', 'Indonesia', 'Irak', 'Iran', 'Irland', 'Island', 'Israel', 'Italia',
		'Jamaica', 'Japan', 'Jemen', 'Jordan',
		'Kambodsja', 'Kamerun', 'Kapp Verde', 'Kasakhstan', 'Kenya', 'Kina', 'Kirgisistan', 'Kiribati', 'Komorene', 'Kosovo', 'Kroatia', 'Kuwait', 'Kypros',
		'Laos', 'Latvia', 'Lesotho', 'Libanon', 'Liberia', 'Libya', 'Liechtenstein', 'Litauen', 'Luxembourg',
		'Madagaskar', 'Makedonia', 'Malawi', 'Malaysia', 'Maldivene', 'Mali', 'Malta', 'Marokko', 'Marshalløyene', 'Mauritania', 'Mauritius', 'Mexico', 'Mikronesiaføderasjonen', 'Moldova', 'Monaco', 'Mongolia', 'Montenegro', 'Mosambik', 'Myanmar',
		'Namibia', 'Nauru', 'Nederland', 'Nepal', 'New Zealand', 'Nicaragua', 'Niger', 'Nigeria', 'Nord-Korea', 'Nord-Kypros', 'Norge',
		'Oman',
		'Pakistan', 'Palau', 'Panama', 'Papua Ny-Guinea', 'Paraguay', 'Peru', 'Polen', 'Portugal',
		'Qatar',
		'Romania', 'Republikken Kongo', 'Russland', 'Rwanda',
		'Saint Kitts og Nevis', 'Saint Lucia', 'Saint Vincent og Grenadinene', 'Salomonøyene', 'Samoa', 'San Marino', 'São Tomé og Príncipe', 'Saudi-Arabia', 'Senegal', 'Serbia', 'Seychellene', 'Sierra Leone', 'Singapore', 'Slovakia', 'Slovenia', 'Somalia', 'Spania', 'Sri Lanka', 'Storbritannia', 'Sudan', 'Surinam', 'Sveits', 'Sverige', 'Swaziland', 'Syria', 'Sør-Afrika', 'Sør-Korea', 'Sør-Ossetia', 'Sør-Sudan',
		'Tadsjikistan', 'Taiwan', 'Tanzania', 'Thailand', 'Togo', 'Tonga', 'Transnistria', 'Trinidad og Tobago', 'Tsjad', 'Tsjekkia', 'Tunisia', 'Turkmenistan', 'Tuvalu', 'Tyrkia', 'Tyskland',
		'Uganda', 'USA', 'Ukraina', 'Ungarn', 'Uruguay', 'Usbekistan',
		'Vanuatu', 'Vatikanstaten', 'Venezuela', 'Vietnam',
		'Zambia', 'Zimbabwe',
		'Østerrike', 'Øst-Timor'
	],

	// ISO 3166-2:NO
	states: [
		'Akershus', 'Aust-Agder', 'Buskerud', 'Finnmark', 'Hedmark', 'Hordaland', 'Møre og Romsdal', 'Nordland', 'Nord-Trøndelag', 'Oppland', 'Oslo', 'Rogaland', 'Sogn og Fjordane', 'Sør-Trøndelag', 'Telemark', 'Troms', 'Vest-Agder', 'Vestfold', 'Østfold'
	],

	// 100 largest cities
	cities: [
		'Oslo', 'Bergen', 'Stavanger', 'Sandnes', 'Trondheim', 'Drammen', 'Fredrikstad', 'Sarpsborg', 'Porsgrunn', 'Skien', 'Kristiansand',
		'Ålesund', 'Tønsberg', 'Moss', 'Haugesund', 'Sandefjord', 'Arendal', 'Bodø', 'Tromsø', 'Hamar', 'Halden',
		'Larvik', 'Askøy', 'Kongsberg', 'Molde', 'Harstad', 'Horten', 'Lillehammer', 'Gjøvik', 'Ski', 'Mo i Rana',
		'Kristiansund', 'Jessheim', 'Korsvik', 'Tromsdalen', 'Hønefoss', 'Elverum', 'Alta', 'Narvik', 'Askim', 'Leirvik',
		'Drøbak', 'Osøyro', 'Vennesla', 'Råholt', 'Nesoddtangen', 'Grimstad', 'Steinkjer', 'Arna', 'Kongsvinger', 'Stjørdalshalsen',
		'Bryne', 'Egersund', 'Lommedalen', 'Kopervik', 'Ålgård', 'Knarrevik', 'Mandal', 'Førde', 'Ås', 'Mosjøen',
		'Levanger', 'Brumunddal', 'Søgne', 'Notodden', 'Florø', 'Kleppe', 'Kvaløysletta', 'Namsos', 'Verdalsøra', 'Orkanger',
		'Fetsund', 'Hammerfest', 'Åkrehamn', 'Lillesand', 'Kløfta', 'Kvernaland', 'Raufoss', 'Holmestrand', 'Vestby', 'Ørsta',
		'Nærbø', 'Jørpeland', 'Malvik', 'Tananger', 'Mysen', 'Hommersåk', 'Vossevangen', 'Åmot', 'Volda', 'Bekkelaget',
		'Melhus', 'Fauske', 'Sandnessjøen', 'Flekkefjord', 'Rotnes', 'Spydeberg', 'Stavern', 'Knarvik', 'Ulsteinvik', 'Kragerø'
	],

	street_suffixes: [
		'vei',
		'gate'
	],

	street_formats: [
		'{{first_name}}s {{street_suffix}}',
		'{{last_name}}s {{street_suffix}}',
		'{{first_name}} {{last_name}}s {{street_suffix}}'
	],

	zip_formats: [
		'####'
	],

	address_formats: [
		'{{street}} {{building_number}}, {{zip}} {{city}}'
	],

	address1_formats: [
		'{{street}} {{building_number}}\n{{zip}} {{city}}',
	],

	address2_formats: [
		'{{first_name}} {{last_name}}\n{{street}} {{building_number}}\n{{zip}} {{city}}',
	],

	country: function () {
		return this.random_element(this.countries);
	},

	state: function () {
		return this.random_element(this.states);
	},

	city: function () {
		return this.random_element(this.cities);
	},

	zip: function () {
		return this.numerify(this.random_element(this.zip_formats));
	},

	street_suffix: function () {
		return this.random_element(this.street_suffixes);
	},

	street: function () {
		return this.populate_one_of(this.street_formats);
	},

	address: function () {
		return this.populate_one_of(this.address_formats);
	},

	address1: function () {
		return this.populate_one_of(this.address1_formats);
	},

	address2: function () {
		return this.populate_one_of(this.address2_formats);
	}

};

module.exports = provider;
