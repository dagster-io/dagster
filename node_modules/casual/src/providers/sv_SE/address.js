var provider = {
	countries: [
		'Afghanistan', 'Albanien', 'Algeriet', 'Andorra', 'Angola',
		'Antigua och Barbuda', 'Argentina', 'Armenien', 'Australien',
		'Azerbajdzjan', 'Azerbajdzjan', 'Bahamas', 'Bahrain', 'Bangladesh',
		'Barbados', 'Belgien', 'Belize', 'Benin', 'Bhutan', 'Bolivia',
		'Bosnien och Hercegovina', 'Botswana', 'Brasilien', 'Brunei',
		'Bulgarien', 'Burkina Faso', 'Burma (Myanmar)', 'Burundi',
		'Centralafrikanska republiken', 'Chile', 'Colombia', 'Costa Rica',
		'Cypern', 'Danmark', 'Demokratiska Republiken Kongo', 'Djibouti',
		'Dominica', 'Dominikanska republiken', 'Ecuador', 'Egypten',
		'Ekvatorialguinea', 'El Salvador', 'Elfenbenskusten', 'Eritrea',
		'Estland', 'Etiopien', 'Fiji', 'Filippinerna', 'Finland', 'Frankrike',
		'Förenade Arabemiraten', 'Förenta staterna, USA', 'Gabon', 'Gambia',
		'Georgien', 'Georgien', 'Ghana', 'Grekland', 'Grenada', 'Guatemala',
		'Guinea-Bissau', 'Guinea', 'Guyana', 'Haiti', 'Honduras', 'Indien',
		'Indonesien', 'Indonesien', 'Irak', 'Iran', 'Irland', 'Island',
		'Israel', 'Italien', 'Jamaica', 'Japan', 'Jemen', 'Jordanien',
		'Kambodja', 'Kamerun', 'Kanada', 'Kap Verde', 'Kazakstan', 'Kazakstan',
		'Kenya', 'Kina', 'Kirgizistan', 'Kiribati', 'Komorerna', 'Kosovo',
		'Kroatien', 'Kuba', 'Kuwait', 'Laos', 'Lesotho', 'Lettland', 'Libanon',
		'Liberia', 'Libyen', 'Liechtenstein', 'Litauen', 'Luxemburg',
		'Madagaskar', 'Makedonien', 'Malawi', 'Malaysia', 'Maldiverna', 'Mali',
		'Malta', 'Marocko', 'Marshallöarna', 'Mauretanien', 'Mauritius',
		'Mexiko', 'Mikronesiens federerade stater', 'Moçambique', 'Moldavien',
		'Monaco', 'Mongoliet', 'Montenegro', 'Namibia', 'Nauru',
		'Nederländerna', 'Nepal', 'Nicaragua', 'Niger', 'Nigeria', 'Nordkorea',
		'Norge', 'Nya Zeeland', 'Oman', 'Pakistan', 'Palau', 'Panama', 'Panama',
		'Papua Nya Guinea', 'Paraguay', 'Peru', 'Polen', 'Portugal', 'Qatar',
		'Republiken Kongo', 'Rumänien', 'Rwanda', 'Ryssland', 'Ryssland',
		'Saint Kitts och Nevis', 'Saint Lucia',
		'Saint Vincent och Grenadinerna', 'Salomonöarna', 'Samoa', 'San Marino',
		'São Tomé och Príncipe', 'Saudiarabien', 'Schweiz', 'Senegal',
		'Serbien', 'Seychellerna', 'Sierra Leone', 'Singapore', 'Slovakien',
		'Slovenien', 'Somalia', 'Spanien', 'Sri Lanka', 'Storbritannien',
		'Sudan', 'Surinam', 'Sverige', 'Swaziland', 'Sydafrika', 'Sydkorea',
		'Syrien', 'Tadzjikistan', 'Taiwan', 'Tanzania', 'Tchad', 'Thailand',
		'Tjeckien', 'Togo', 'Tonga', 'Trinidad och Tobago', 'Tunisien',
		'Turkiet', 'Turkiet', 'Turkmenistan', 'Tuvalu', 'Tyskland', 'Uganda',
		'Ukraina', 'Ungern', 'Uruguay', 'Uzbekistan', 'Vanuatu',
		'Vatikanstaten', 'Venezuela', 'Vietnam', 'Vitryssland',
		'Västsahara (ockuperat av Marocko)', 'Zambia', 'Zimbabwe', 'Österrike',
		'Östtimor',
	],

	counties: [
		'Blekinge', 'Dalarna', 'Gotland', 'Gävleborg', 'Halland', 'Jämtland',
		'Jönköping', 'Kalmar', 'Kronoberg', 'Norrbotten', 'Skåne', 'Stockholm',
		'Södermanland', 'Uppsala', 'Värmland', 'Västerbotten', 'Västernorrland',
		'Västmanland', 'Västra Götaland', 'Örebro', 'Östergötland',
	],

	real_cities: [
		'Stockholm', 'Göteborg', 'Malmö', 'Uppsala', 'Västerås', 'Örebro',
		'Linköping', 'Helsingborg', 'Jönköping', 'Norrköping', 'Lund', 'Umeå',
		'Gävle', 'Borås', 'Södertälje', 'Eskilstuna', 'Halmstad', 'Växjö',
		'Karlstad', 'Sundsvall', 'Östersund', 'Trollhättan', 'Luleå', 'Lidingö',
		'Borlänge', 'Tumba', 'Kristianstad', 'Kalmar', 'Falun', 'Skövde',
		'Karlskrona', 'Skellefteå', 'Uddevalla', 'Varberg', 'Åkersberga',
		'Örnsköldsvik', 'Landskrona', 'Nyköping', 'Vallentuna', 'Motala',
		'Trelleborg', 'Ängelholm', 'Karlskoga', 'Märsta', 'Lerum', 'Alingsås',
		'Sandviken', 'Laholm',
	],

	city_suffixes: [
		'holm', 'borg', 'bro', 'stad', 'sund', 'krona', 'berg', 'vik', 'hamn',
		'näs', 'hammar', 'torp',
	],

	street_prefixes: [
		'Hantverks', 'Viol', 'Blomster', 'Bro', 'Stor', 'Drottnings', 'Kungs',
		'Solo', 'Stålverks', 'Furu', 'Dala', 'Ene', 'Hjort', 'Asp', 'Tall',
		'Lärk', 'Murare', 'Järnvägs', 'Hamn', 'Odal', 'Skol', 'Svetsare',
	],

	street_suffixes: [
		'väg', 'vägen', 'gränd', 'gränden', 'gatan', 'stig', 'stigen', 'gången',
	],

	zip_formats: ['#####', '### ##'],

	building_number_formats: [
		'#', '##', '###', '####',
		'#A', '#B', '#C', '#D', '#E', '#F',
		'##A', '##B', '##C', '##D', '##E', '##F',
	],

	city_formats: [
		'{{real_city}}',
		'{{first_name}}{{city_suffix}}',
	],

	street_formats: [
		'{{street_prefix}}{{street_suffix}}',
		'{{first_name}}{{street_suffix}}',
		'{{last_name}}{{street_suffix}}',
	],

	address1_formats: [
		'{{street}} {{building_number}}',
		'{{street}} {{building_number}} {{address2}}',
	],

	address2_formats: ['Lgh ####'],

	address_formats: [
		'{{address1}}\n{{zip}} {{city}}',
	],

	city_suffix: function() {
		return this.random_element(this.city_suffixes);
	},

	real_city: function() {
		return this.random_element(this.real_cities);
	},

	street_prefix: function() {
		return this.random_element(this.street_prefixes);
	},

	street_suffix: function() {
		return this.random_element(this.street_suffixes);
	},

	street: function() {
		return this.populate_one_of(this.street_formats);
	},

	county: function() {
		return this.random_element(this.counties);
	},
};

module.exports = provider;
