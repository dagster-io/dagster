var provider = {
	states: ['Schleswig-Holstein', 'Mecklenburg-Vorpommern', 'Hamburg', 'Bremen', 'Niedersachsen', 'Brandenburg', 'Berlin', 'Sachsen-Anhalt', 'Sachsen', 'Thüringen', 'Hessen', 'Rheinland-Pfalz', 'Nordrhein-Westfalen', 'Saarland', 'Baden-Württemberg', 'Bayern'],

	// Abbreviations taken from each state's Wikipedia page
	state_abbrs: ['SH', 'MV', 'HH', 'HB', 'Nds.', 'BB', 'BER', 'ST', 'Sa.', 'TH', 'HE', 'RLP', 'NRW', 'SL', 'BW', 'BY'],

	// Parts for city names are extracted from the 200 biggest cities' names from https://de.wikipedia.org/wiki/Liste_der_Gro%C3%9F-_und_Mittelst%C3%A4dte_in_Deutschland
	city_prefixes: ['Neu', 'Alt', 'St.', 'Sankt', 'Groß', 'Klein', 'Ober', 'Unter', 'Nieder', 'Bad'],

	city_parts: ['Ham', 'Mün', 'Frank', 'Düssel', 'Stutt', 'Dort', 'Leip', 'Nürn', 'Duis', 'Wupper', 'Biele', 'Karls', 'Mann', 'Augs', 'Wies', 'Gelsen', 'Mönchen', 'Braun', 'Madge', 'Kre', 'Frei', 'Lü', 'Ober', 'Er', 'Ro', 'Saar', 'Mül', 'Olden', 'Sol', 'Pots', 'Lever', 'Ludwigs', 'Osna', 'Heidel', 'Darm', 'Pader', 'Regens', 'Ingol', 'Würz', 'Wolfs', 'Offen', 'Heil', 'Gött', 'Reck', 'Reut', 'Kob', 'Rem', 'Bremer', 'Cott', 'Hildes', 'Salz', 'Kaisers', 'Güters', 'Iser', 'Ludwigs', 'Ha', 'Zwick', 'Rat', 'Tüb', 'Flens', 'Norder', 'Wilhelms', 'Glad', 'Delmen', 'Trois', 'Mar', 'Arns', 'Lüden', 'Lüne', 'Bay', 'Bam', 'Aschaffen', 'Dins', 'Lipp', 'Lands', 'Her', 'Neubranden', 'Greven', 'Rosen', 'Friedrichs', 'Langen', 'Greifs', 'Göpp', 'Eus', 'Esch', 'Meer', 'Hatt', 'Hom', 'Schwein', 'Wolfen', 'Gummers', 'Ravens', 'Erft', 'Cux', 'Oeyn', 'Franken'],

	city_suffixes: ['burg', 'stadt', 'städt', 'bach', 'berg', 'bergen', 'beck', 'hellen', 'heim', 'ing', 'ingen', 'hausen', 'chen', 'gart', 'mund', 'zig', 'tal', 'feld', 'ruhe', 'baden', 'kirchen', 'gladbach', 'bach', 'schweig', 'furt', 'stock', 'brücken', 'brück', 'damm', 'kusen', 'hafen', 'born', 'bronn', 'lenz', 'scheid', 'bus', 'gitter', 'lautern', 'loh', 'horst', 'laken', 'hut', 'ford', 'broich', 'wald', 'weiler', 'busch', 'lar', 'lich', 'lichen', 'stein', 'büttel', 'hagen', 'uflen', 'stin', 'litz'],

	city_suffix_words: ['am Main', '(Main)', 'an der Saale', '(Saale)', 'im Breisgau', '(Breisgau)', 'an der Ruhr', 'a.d.R.', '(Ruhr)', 'an der Donau', '(Donau)', 'am Rhein', '(Rhein)', 'am Neckar', '(Neckar)', 'an der Havel', '(Havel)', 'im Allgäu', '(Allgäu)', 'an der Oder', '(Oder)', 'im Rheinland', '(Rheinland)', 'im Sauerland', '(Sauerland)', 'an der Weinstraße', 'vor der Höhe', 'an der Ems', '(Ems)', 'in der Pfalz', '(Pfalz)'],

	street_suffixes: ['allee', 'straße', 'str.', 'weg', 'gasse', 'aue', 'platz', 'park'],

	// adapted from the most common street names taken from http://www.strassen-in-deutschland.de/die-haeufigsten-strassennamen-in-deutschland.html
	street_parts: ['Eichen', 'Rosen', 'Feld', 'Blumen', 'Mühlen', 'Friedhof', 'Erlen', 'Tannen', 'Mozart', 'Brunnen', 'Linden', 'Bach', 'Raiffeisen', 'Rosen', 'Drossel', 'Kirch', 'Lerchen', 'Mühlen', 'Tal', 'Beethoven', 'Industrie', 'Mittel', 'Post', 'Meisen', 'Garten', 'Breslauer', 'Flieder', 'Lessing', 'Wald', 'Kirch', 'Uhland', 'Schloß', 'Königsberger', 'Birken', 'Kirchplatz', 'Fasanen', 'Burg', 'Kiefern', 'Tulpen', 'Danziger', 'Bahnhof', 'Neue', 'Kastanien', 'Park', 'Winkel', 'Marktplatz', 'Schul', 'Schützen', 'Berliner', 'Mühl', 'Römer', 'Grüner', 'Kapellen', 'Mittel', 'Nelken', 'Eschen', 'Heide', 'Fichten', 'Stettiner', 'Ulmen', 'Schubert', 'Wilhelm', 'Sudeten', 'Sonnen', 'Friedrich', 'Marien', 'Anger', 'Eichen', 'Lärchen', 'Eichendorff', 'Brücken', 'Hang', 'Markt', 'Ginster', 'Friedhofs', 'Kurze', 'Nord', 'Schwalben', 'Lange', 'Ahorn', 'Flur', 'Kolping', 'Neuer', 'Karl', 'Stein', 'Pappel', 'Holunder', 'Süd', 'Akazien', 'Buchen', 'Kapellen', 'Rathaus', 'Kant', 'Hoch', 'Pestalozzi', 'Mühl', 'Tulpen', 'Höhen', 'Brunnen', 'See', 'Friedens', 'Kreuz', 'Quer', 'Stein', 'Weiden', 'Sonnen', 'Gutenberg', 'Nelken', 'Falken', 'Pfarr', 'Sand', 'Astern', 'Frieden', 'Weinberg', 'Zeppelin', 'Dahlien', 'Schlehen', 'Grenz', 'Franken', 'Haydn', 'Mörike', 'Teich', 'Kloster', 'Graben', 'Veilchen', 'Lerchen', 'Ost', 'Siedlung', 'Schwarzer', 'Staren', 'Siemens', 'Fichten', 'Wacholder', 'Jäger', 'Hölderlin', 'Forst', 'Markt', 'Bismarck', 'Ludwig', 'Lilien', 'Wiesengrund', 'Tannen', 'Hecken', 'Berg', 'Burg', 'Leipziger', 'Hohl', 'Mühl', 'Hohe', 'Weiher', 'Daimler', 'Blumen', 'Diesel', 'West', 'Ulmen', 'Erlen', 'Forst', 'Rhein', 'Rotdorn', 'Lindenallee', 'Luisen', 'Finken', 'Kirchen', 'Kreuz', 'Frühlings'],

	countries: ['Afghanistan', 'Ägypten', 'Åland', 'Albanien', 'Algerien', 'Amerikanische Jungferninseln', 'Amerikanisch-Samoa', 'Andorra', 'Angola', 'Anguilla', 'Antarktika', 'Antigua und Barbuda', 'Äquatorialguinea', 'Argentinien', 'Armenien', 'Aruba', 'Aserbaidschan', 'Äthiopien', 'Australien', 'Bahamas', 'Bahrain', 'Bangladesch', 'Barbados', 'Bassas da India', 'Belarus', 'Belgien', 'Belize', 'Benin', 'Bermuda', 'Bhutan', 'Bolivien', 'Bosnien und Herzegowina', 'Botsuana', 'Bouvetinsel', 'Brasilien', 'Britische Jungferninseln', 'Britisches Territorium im Indischen Ozean', 'Brunei Darussalam', 'Bulgarien', 'Burkina Faso', 'Burundi', 'Chile', 'China', 'Clipperton', 'Cookinseln', 'Costa Rica', 'Côte d\'Ivoire', 'Dänemark', 'Deutschland', 'Dominica', 'Dominikanische Republik', 'Dschibuti', 'Ecuador', 'El Salvador', 'Eritrea', 'Estland', 'Europa', 'FalklandinselnF', 'Färöer', 'Fidschi', 'Finnland', 'Frankreich', 'Frankreich (metropolitanes)', 'Französische Süd- und Antarktisgebiete', 'Französisch-Guayana', 'Französisch-Polynesien', 'Gabun', 'Gambia', 'Gazastreifen', 'Georgien', 'Ghana', 'Gibraltar', 'Glorieuses', 'Grenada', 'Griechenland', 'Grönland', 'Großbritannien', 'Guadeloupe', 'Guam', 'Guatemala', 'Guernsey', 'Guinea', 'Guinea-Bissau', 'Guyana', 'Haiti', 'Heard und McDonaldinseln', 'Honduras', 'Hongkong', 'Indien', 'Indonesien', 'Insel Man', 'Irak', 'Iran', 'Irland', 'Island', 'Israel', 'Italien', 'Jamaika', 'Japan', 'Jemen', 'Jersey', 'Jordanien', 'Juan de Nova', 'Kaimaninseln', 'Kambodscha', 'Kamerun', 'Kanada', 'Kap Verde', 'Kasachstan', 'Katar', 'Kenia', 'Kirgisistan', 'Kiribati', 'Kleinere Amerikanische Überseeinseln', 'Kokosinseln (Keelinginseln)', 'Kolumbien', 'Komoren', 'Kongo', 'Kongo, Demokratische Republik', 'Korea, Demokratische Volksrepublik', 'Korea, Republik', 'Kroatien', 'Kuba', 'Kuwait', 'Laos', 'Lesotho', 'Lettland', 'Libanon', 'Liberia', 'Libyen', 'Liechtenstein', 'Litauen', 'Luxemburg', 'Macau', 'Madagaskar', 'Malawi', 'Malaysia', 'Malediven', 'Mali', 'Malta', 'Marokko', 'Marshallinseln', 'Martinique', 'Mauretanien', 'Mauritius', 'Mayotte', 'Mazedonien', 'Mexiko', 'Mikronesien', 'Moldau', 'Monaco', 'Mongolei', 'Montenegro', 'Montserrat', 'Mosambik', 'Myanmar', 'Namibia', 'Nauru', 'Nepal', 'Neukaledonien', 'Neuseeland', 'Nicaragua', 'Niederlande', 'Niederländische Antillen', 'Niger', 'Nigeria', 'Niue', 'Nördliche Marianen', 'Norfolkinsel', 'Norwegen', 'Oman', 'Österreich', 'Pakistan', 'Palau', 'Panama', 'Papua-Neuguinea', 'Paraguay', 'Peru', 'Philippinen', 'Pitcairninseln', 'Polen', 'Portugal', 'Puerto Rico', 'Réunion', 'Ruanda', 'Rumänien', 'Russische Föderation', 'Saint-Martin', 'Salomonen', 'Sambia', 'Samoa', 'San Marino', 'São Tomé und Príncipe', 'Saudi-Arabien', 'Schweden', 'Schweiz', 'Senegal', 'Serbien', 'Serbien und Montenegro', 'Seychellen', 'Sierra Leone', 'Simbabwe', 'Singapur', 'Slowakei', 'Slowenien', 'Somalia', 'Spanien', 'Spitzbergen', 'Sri Lanka', 'St. Barthélemy', 'St. Helena, Ascension und Tristan da Cunha', 'St. Kitts und Nevis', 'St. Lucia', 'St. Pierre und Miquelon', 'St. Vincent und die Grenadinen', 'Südafrika', 'Sudan', 'Südgeorgien und die Südlichen Sandwichinseln', 'Südsudan', 'Suriname', 'Swasiland', 'Syrien', 'Tadschikistan', 'Taiwan', 'Tansania', 'Thailand', 'Timor-Leste', 'Togo', 'Tokelau', 'Tonga', 'Trinidad und Tobago', 'Tromelin', 'Tschad', 'Tschechische Republik', 'Tunesien', 'Türkei', 'Turkmenistan', 'Turks- und Caicosinseln', 'Tuvalu', 'Uganda', 'Ukraine', 'Ungarn', 'Uruguay', 'Usbekistan', 'Vanuatu', 'Vatikanstadt', 'Venezuela', 'Vereinigte Arabische Emirate', 'Vereinigte Staaten', 'Vietnam', 'Wallis und FutunaWF', 'Weihnachtsinsel', 'Westjordanland', 'Westsahara', 'Zentralafrikanische Republik', 'Zypern'],

	city_formats: [
		'{{city_prefix}} {{city_part}}{{city_suffix}}',
		'{{city_part}}{{city_suffix}}',
		'{{city_part}}{{city_suffix}} {{city_suffix_word}}'
	],

	// German ZIPs don't have more than one leading 0, so this could produce invalid ZIPs like 00123
	zip_formats: ['#####', 'DE-#####'],

	building_number_formats: ['#{{building_number_letter}}', '##{{building_number_letter}}', '###{{building_number_letter}}'],

	// anything above 'h' is pretty uncommon
	building_number_letters: ['', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'],

	street_formats: [
		'{{street_part}}{{street_suffix}}',
		'Auf dem {{street_part}}weg',
		'An der {{street_part}}aue',
		'Obere {{street_part}}straße',
		'Kleine {{street_part}}gasse',
		'Alte {{street_part}}allee',
		'Am {{street_part}}park'
	],

	address1_formats: [
		'{{street}} {{building_number}}',
		'{{street}} {{building_number}} ({{address2}})'
	],

	address2_formats: ['EG', 'EG links', 'EG rechts', '#. OG', '#. OG links', '#. OG rechts'],

	address_formats: [
		'{{address1}}\n{{zip}} {{city}}',
		'{{address1}}\n{{zip}} {{city}}\n{{state_abbr}}',
		'{{address1}}\n{{zip}} {{city}}\n{{state}}',
	],

	state: function() {
		return this.random_element(this.states);
	},

	state_abbr: function() {
		return this.random_element(this.state_abbrs);
	},

	street_part: function() {
		return this.random_element(this.street_parts);
	},

	city_part: function() {
		return this.random_element(this.city_parts);
	},

	city_suffix_word: function() {
		return this.random_element(this.city_suffix_words);
	},

	// German zips always have 5 digits, so this implementation ignores the digits parameter
	zip: function() {
		return this.numerify(this.random_element(this.zip_formats));
	},

	building_number: function() {
		return this.numerify(this.populate_one_of(this.building_number_formats));
	},

	building_number_letter: function() {
		return this.random_element(this.building_number_letters);
	}
};

module.exports = provider;
