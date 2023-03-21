var provider = {
	countries: [
		'Afghanistan', 'Albanië', 'Algerije', 'Andorra', 'Angola', 'Antigua en Barbuda', 'Argentinië', 'Armenië', 'Australië', 'Azerbeidzjan',
		'Bahama\'s', 'Bahrein', 'Bangladesh', 'Barbados', 'België', 'Belize', 'Benin', 'Bhutan', 'Bolivië', 'Bosnië-Herzegovina', 'Botswana', 'Brazilië', 'Brunei', 'Bulgarije', 'Burkina Faso', 'Burundi',
		'Cambodja', 'Canada', 'Centraal-Afrikaanse Republiek', 'Chili', 'China', 'Colombia', 'Comoren', 'Congo-Brazzaville', 'Congo-Kinshasa', 'Costa Rica', 'Cuba', 'Cyprus',
		'Denemarken', 'Djibouti', 'Dominica', 'Dominicaanse Republiek', 'Duitsland',
		'Ecuador', 'Egypte', 'El Salvador', 'Equatoriaal-Guinea', 'Eritrea', 'Estland', 'Ethiopië',
		'Fiji', 'Filipijnen', 'Finland', 'Frankrijk',
		'Gabon', 'Gambia', 'Georgië', 'Ghana', 'Grenada', 'Griekenland', 'Guatemala', 'Guinea', 'Guinee-Bissau', 'Guyana',
		'Haïti', 'Honduras', 'Hongarije',
		'Ierland', 'IJsland', 'India', 'Indonesië', 'Irak', 'Iran', 'Israël', 'Italië', 'Ivoorkust',
		'Jamaica', 'Japan', 'Jemen', 'Jordanië',
		'Kaapverdië', 'Kameroen', 'Kazachstan', 'Kenia', 'Kirgizië', 'Kiribati', 'Koeweit', 'Kroatië',
		'Laos', 'Lesotho', 'Letland', 'Libanon', 'Liberia', 'Libië', 'Liechtenstein', 'Litouwen', 'Luxemburg',
		'Macedonië', 'Madagaskar', 'Malawi', 'Maldiven', 'Maleisië', 'Mali', 'Malta', 'Marokko', 'Mauritanië', 'Mauritius', 'Mayotte', 'Mexico', 'Micronesia', 'Moldavië', 'Monaco', 'Mongolië', 'Montenegro', 'Mozambique', 'Myanmar',
		'Namibië', 'Nauru', 'Nederland', 'Nepal', 'Nicaragua', 'Nieuw-Zeeland', 'Niger', 'Nigeria', 'Noord-Korea', 'Noorwegen', 'Norfolk Island',
		'Oeganda', 'Oekraïne', 'Oezbekistan', 'Oman', 'Oostenrijk', 'Oost-Timor',
		'Pakistan', 'Palau', 'Palestina', 'Panama', 'Papoea-Nieuw-Guinea', 'Paraguay', 'Peru', 'Polen', 'Portugal',
		'Qatar',
		'Roemenië', 'Rusland', 'Rwanda',
		'Sint-Kitts en Nevis', 'Saint Lucia', 'Saint Vincent en de Grenadines', 'Salomonseilanden', 'Samoa', 'San Marino', 'São Tomé en Principe', 'Saudi-Arabië', 'Senegal', 'Servië', 'Seychellen', 'Sierra Leone', 'Singapore', 'Slovenië', 'Slowakije', 'Soedan', 'Somalië', 'Spanje', 'Sri Lanka', 'Suriname', 'Swaziland', 'Syrië',
		'Tadzjikistan', 'Tanzania', 'Thailand', 'Togo', 'Tonga', 'Trinidad en Tobago', 'Tsjaad', 'Tsjechië', 'Tunesië', 'Turkije', 'Turkmenistan', 'Tuvalu',
		'Uruguay',
		'Vanuatu', 'Vaticaanstad', 'Venezuela', 'Verenigd Koninkrijk', 'Verenigde Arabische Emiraten', 'Verenigde Staten', 'Vietnam', 'Wit Rusland',
		'Zambia', 'Zimbabwe', 'Zuid-Afrika', 'Zuid-Korea', 'Zuid-Soedan', 'Zweden', 'Zwitserland'
	],

	// The official name of 'Brabant' is actually 'Noord-Brabant', but 'Brabant' is more commonly used.
	states: ['Drenthe', 'Flevoland', 'Friesland', 'Gelderland', 'Groningen', 'Limburg', 'Brabant', 'Noord-Holland', 'Overijssel', 'Utrecht', 'Zeeland', 'Zuid-Holland'],

	// ISO 3166-2:NL
	state_abbrs: ['DR', 'FL', 'FR', 'GE', 'GR', 'LI', 'NB', 'NH', 'OV', 'UT', 'ZE', 'ZH'],

	// First three cities of each letter in the alphabet
	cities: [
		'Aa en Hunze', 'Aalburg', 'Aalsmeer',
		'Baarle-Nassau', 'Baarn', 'Barendrecht',
		'Capelle aan den IJssel', 'Castricum', 'Coevorden',
		'Dalfsen', 'Dantumadeel', 'De Bilt',
		'Echt-Susteren', 'Edam-Volendam', 'Ede',
		'Ferwerderadeel', 'Franekeradeel',
		'Geertruidenberg', 'Geldermalsen', 'Geldrop-Mierlo',
		'Haaksbergen', 'Haaren', 'Haarlem',
		'IJsselstein',
		'Kaag en Braassem', 'Kampen', 'Kapelle',
		'Laarbeek', 'Landerd', 'Landgraaf',
		'Maasdonk', 'Maasdriel', 'Maasgouw',
		'Naarden', 'Neder-Betuwe', 'Nederlek',
		'Oegstgeest', 'Oirschot', 'Oisterwijk',
		'Papendrecht', 'Peel en Maas', 'Pekela',
		'Raalte', 'Reimerswaal', 'Renkum',
		'Schagen', 'Schermer', 'Scherpenzeel',
		'Ten Boer', 'Terneuzen', 'Terschelling',
		'Ubbergen', 'Uden', 'Uitgeest',
		'Vaals', 'Valkenburg aan de Geul', 'Valkenswaard',
		'Waalre', 'Waalwijk', 'Waddinxveen',
		'Zaanstad', 'Zaltbommel', 'Zandvoort'
	],

	street_suffixes: ['dijk', 'dwarsstraat', 'gracht', 'kade', 'laan', 'plein', 'singel', 'straat', 'steeg', 'wal'],

	address1_formats: [
		'{{street}} {{building_number}}'
	],

	address_formats: [
		'{{address1}}\n {{zip}} {{city}}, {{state}}',
	],

	zip_formats: ['####'],

	zip: function() {
		return this.numerify(this.random_element(this.zip_formats)) + ' ' + (this._letter() + this._letter()).toUpperCase();
	},

	city: function() {
		return this.random_element(this.cities);
	}
};

module.exports = provider;
