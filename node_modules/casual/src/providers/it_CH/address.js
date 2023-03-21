var provider = {

  countries: ['Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua e Barbuda', 'Arabia Saudita', 'Argentina', 'Armenia', 'Australia', 'Austria', 'Azerbaigian', 'Bahamas', 'Bahrein', 'Bangladesh', 'Barbados', 'Belarus', 'Belgio', 'Belize', 'Benin', 'Bhutan', 'Bielorussia', 'Bolivia', 'Bosnia e Erzegovina', 'Botswana', 'Brasile', 'Brunei Darussalam', 'Bulgaria', 'Burkina Faso', 'Burundi', 'Cambogia', 'Camerun', 'Canada', 'Capo Verde', 'Repubblica ceca', 'Repubblica centrafricana', 'Ciad', 'Cile', 'Cina', 'Cipro', 'Colombia', 'Comore', 'Congo (Brazzaville)', 'Congo (Kinshasa)', 'Cook Islands', 'Corea (Nord)', 'Corea (Sud)', 'Costa d\'Avorio', 'Costa Rica', 'Croazia', 'Cuba', 'Côte d\'Ivoire', 'Danimarca', 'Dominica', 'Repubblica dominicana', 'Ecuador', 'Egitto', 'El Salvador', 'Emirati arabi uniti', 'Eritrea', 'Estonia', 'Etiopia', 'Figi', 'Finlandia', 'Filippine', 'Francia', 'Gabon', 'Gambia', 'Georgia', 'Germania', 'Ghana', 'Giamaica', 'Giappone', 'Gibuti', 'Giordania', 'Gran Bretagna', 'Grecia', 'Grenada', 'Guatemala', 'Guinea', 'Guinea equatoriale', 'Guinea-Bissau', 'Guyana', 'Haiti', 'Honduras', 'India', 'Indonesia', 'Iran', 'Iraq', 'Irlanda', 'Islanda', 'Israele', 'Italia', 'Kazakstan', 'Kenia', 'Kirghizistan', 'Kiribati', 'Kosovo', 'Kuwait', 'Laos', 'Lesotho', 'Lettonia', 'Libano', 'Liberia', 'Libia', 'Liechtenstein', 'Lituania', 'Lussemburgo', 'Macedonia', 'Madagascar', 'Malawi', 'Malaysia', 'Maldive', 'Mali', 'Malta', 'Marocco', 'Isole Marshall', 'Mauritania', 'Maurizio', 'Messico', 'Micronesia', 'Moldova', 'Monaco', 'Mongolia', 'Montenegro', 'Mozambico', 'Myanmar', 'Namibia', 'Nauru', 'Nepal', 'Nicaragua', 'Niger', 'Nigeria', 'Norvegia', 'Nuova Zelanda', 'Oman', 'Paesi Bassi', 'Pakistan', 'Palau', 'Panama', 'Papua Nuova Guinea', 'Paraguay', 'Perù', 'Polonia', 'Portogallo', 'Qatar', 'Romania', 'Ruanda', 'Russia', 'Saint Kitts e Nevis', 'Saint Lucia', 'Saint Vincent e Grenadine', 'Isole Salomone', 'Samoa', 'San Marino', 'São Tomé e Príncipe', 'Seicelle', 'Senegal', 'Serbia', 'Sierra Leone', 'Singapore', 'Siria', 'Slovacchia', 'Slovenia', 'Somalia', 'Spagna', 'Sri Lanka', 'Stati Uniti d\'America', 'Sudafrica', 'Sudan', 'Sudan del Sud', 'Suriname', 'Svezia', 'Swaziland', 'Tagikistan', 'Taiwan', 'Tanzania', 'Territorio Palestinese Occupato', 'Thailandia', 'Timor-Leste', 'Togo', 'Tonga', 'Trinidad e Tobago', 'Tunisia', 'Turchia', 'Turkmenistan', 'Tuvalu', 'Ucraina', 'Uganda', 'Ungheria', 'Uruguay', 'Uzbekistan', 'Vanuatu', 'Venezuela', 'Vietnam', 'Yemen', 'Zambia', 'Zimbabwe'],

  states: ['Zurigo', 'Berna', 'Lucerna', 'Uri', 'Svitto', 'Obvaldo', 'Nidvaldo', 'Glarona', 'Zugo', 'Friburgo', 'Soletta', 'Basilea Città', 'Basilea Campagna', 'Sciaffusa', 'Appenzello Esterno', 'Appenzello Interno', 'San Gallo', 'Grigioni', 'Argovia', 'Turgovia', 'Ticino', 'Vaud', 'Vallese', 'Neuchâtel', 'Ginevra', 'Giura'],

  state_abbrs: ['ZH', 'BE', 'LU', 'UR', 'SZ', 'OW', 'NW', 'GL', 'ZG', 'FR', 'SO', 'BS', 'BL', 'SH', 'AR', 'AI', 'SG', 'GR', 'AG', 'TG', 'TI', 'VD', 'VS', 'NE', 'GE', 'JU'],

  cities: ['Zurigo', 'Ginevra', 'Basilea', 'Losanna', 'Berna', 'Winterthur', 'Lucerna', 'San Gallo', 'Lugano', 'Bienne', 'Thun', 'Köniz', 'La Chaux-de-Fonds', 'Sciaffusa', 'Friburgo', 'Coira', 'Neuchâtel', 'Vernier', 'Uster', 'Sion', 'Lancy', 'Emmen', 'Yverdon-les-Bains', 'Zugo', 'Kriens', 'Rapperswil-Jona', 'Dübendorf', 'Montreux', 'Dietikon', 'Frauenfeld', 'Wetzikon', 'Baar', 'Meyrin', 'Riehen', 'Wädenswil', 'Wettingen', 'Carouge', 'Renens', 'Kreuzlingen', 'Aarau', 'Allschwil', 'Bulle', 'Horgen', 'Nyon', 'Reinach', 'Vevey', 'Kloten', 'Wil', 'Baden', 'Gossau', 'Onex', 'Bülach', 'Volketswil', 'Bellinzona', 'Muttenz', 'Thalwil', 'Pully', 'Olten', 'Regensdorf', 'Adliswil', 'Monthey', 'Schlieren', 'Martigny', 'Soletta', 'Grenchen', 'Freienbach', 'Illnau-Effretikon', 'Opfikon', 'Sierre', 'Ostermundigen', 'Steffisburg', 'Burgdorf', 'Pratteln', 'Herisau', 'Locarno', 'Langenthal', 'Cham', 'Morges', 'Binningen', 'Wohlen', 'Svitto', 'Einsiedeln', 'Stäfa', 'Wallisellen', 'Arbon', 'Liestal', 'Thônex', 'Küsnacht', 'Horw', 'Versoix', 'Uzwil', 'Muri bei Bern', 'Meilen', 'Spiez', 'Briga-Glis', 'Richterswil', 'Oftringen', 'Amriswil', 'Küssnacht', 'Ebikon'],

  street_suffixes: ['Stefano Franscini', 'Stazione', 'del Tiglio', 'Lungolago', 'Miranda', 'Morettina', 'delle Scuole', 'Regazzoni', 'della Pace', 'Lavizzari', 'San Biagio', 'Cantonale', 'Rinaldo Simen'],

  zip_formats: ['####', 'CH-####'],

  building_number_formats: ['##', '###'],

  street_formats: [
    'Via {{street_suffix}}',
    'Piazza {{street_suffix}}'
  ],

  address1_formats: [
    '{{street}}',
    '{{street}} {{address2}}'
  ],

  address2_formats: ['#', '##'],

  address_formats: [
    '{{address1}}\n{{zip}} {{city}}',
  ],

  city: function() {
    return this.populate_one_of(this.cities);
  },

};

module.exports = provider;
