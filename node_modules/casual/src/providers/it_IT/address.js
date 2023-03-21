var provider = {

  countries: ['Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua e Barbuda', 'Arabia Saudita', 'Argentina', 'Armenia', 'Australia', 'Austria', 'Azerbaigian', 'Bahamas', 'Bahrein', 'Bangladesh', 'Barbados', 'Bielorussia', 'Belgio', 'Belize', 'Benin', 'Bhutan', 'Bielorussia', 'Bolivia', 'Bosnia e Erzegovina', 'Botswana', 'Brasile', 'Brunei Darussalam', 'Bulgaria', 'Burkina Faso', 'Burundi', 'Cambogia', 'Camerun', 'Canada', 'Capo Verde', 'Repubblica Ceca', 'Repubblica Centrafricana', 'Ciad', 'Cile', 'Cina', 'Cipro', 'Colombia', 'Comore', 'Congo (Brazzaville)', 'Congo (Kinshasa)', 'Isole Cook', 'Corea (Nord)', 'Corea (Sud)', 'Costa d\'Avorio', 'Costa Rica', 'Croazia', 'Cuba', 'Danimarca', 'Dominica', 'Repubblica Dominicana', 'Ecuador', 'Egitto', 'El Salvador', 'Emirati arabi uniti', 'Eritrea', 'Estonia', 'Etiopia', 'Figi', 'Finlandia', 'Filippine', 'Francia', 'Gabon', 'Gambia', 'Georgia', 'Germania', 'Ghana', 'Giamaica', 'Giappone', 'Gibuti', 'Giordania', 'Gran Bretagna', 'Grecia', 'Grenada', 'Guatemala', 'Guinea', 'Guinea equatoriale', 'Guinea-Bissau', 'Guyana', 'Haiti', 'Honduras', 'India', 'Indonesia', 'Iran', 'Iraq', 'Irlanda', 'Islanda', 'Israele', 'Italia', 'Kazakistan', 'Kenya', 'Kirghizistan', 'Kiribati', 'Kosovo', 'Kuwait', 'Laos', 'Lesotho', 'Lettonia', 'Libano', 'Liberia', 'Libia', 'Liechtenstein', 'Lituania', 'Lussemburgo', 'Macedonia', 'Madagascar', 'Malawi', 'Malesia', 'Maldive', 'Mali', 'Malta', 'Marocco', 'Isole Marshall', 'Mauritania', 'Mauritius', 'Messico', 'Micronesia', 'Moldavia', 'Monaco', 'Mongolia', 'Montenegro', 'Mozambico', 'Myanmar', 'Namibia', 'Nauru', 'Nepal', 'Nicaragua', 'Niger', 'Nigeria', 'Norvegia', 'Nuova Zelanda', 'Oman', 'Paesi Bassi', 'Pakistan', 'Palau', 'Panama', 'Papua Nuova Guinea', 'Paraguay', 'Perù', 'Polonia', 'Portogallo', 'Qatar', 'Romania', 'Ruanda', 'Russia', 'Saint Kitts e Nevis', 'Saint Lucia', 'Saint Vincent e Grenadine', 'Isole Salomone', 'Samoa', 'San Marino', 'São Tomé e Príncipe', 'Seicelle', 'Senegal', 'Serbia', 'Sierra Leone', 'Singapore', 'Siria', 'Slovacchia', 'Slovenia', 'Somalia', 'Spagna', 'Sri Lanka', 'Stati Uniti d\'America', 'Sudafrica', 'Sudan', 'Sudan del Sud', 'Suriname', 'Svezia', 'Swaziland', 'Tagikistan', 'Taiwan', 'Tanzania', 'Territorio Palestinese Occupato', 'Thailandia', 'Timor Est', 'Togo', 'Tonga', 'Trinidad e Tobago', 'Tunisia', 'Turchia', 'Turkmenistan', 'Tuvalu', 'Ucraina', 'Uganda', 'Ungheria', 'Uruguay', 'Uzbekistan', 'Vanuatu', 'Venezuela', 'Vietnam', 'Yemen', 'Zambia', 'Zimbabwe'],

  states: ['Agrigento', 'Alessandria', 'Ancona', 'Valle d\'Aosta', 'Arezzo', 'Ascoli Piceno', 'Asti', 'Avellino', 'Barletta-Andria-Trani', 'Belluno', 'Benevento', 'Bergamo', 'Biella', 'Bolzano', 'Brescia', 'Brindisi', 'Caltanissetta', 'Campobasso', 'Caserta', 'Catanzaro', 'Chieti', 'Como', 'Cosenza', 'Cremona', 'Crotone', 'Cuneo', 'Enna', 'Fermo', 'Ferrara', 'Foggia', 'Forlì-Cesena', 'Frosinone', 'Gorizia', 'Grosseto', 'Imperia', 'Isernia', 'La Spezia', 'L\'Aquila', 'Latina', 'Lecce', 'Lecco', 'Livorno', 'Lodi', 'Lucca', 'Macerata', 'Mantova', 'Massa Carrara', 'Matera', 'Modena', 'Monza Brianza', 'Novara', 'Nuoro', 'Oristano', 'Padova', 'Parma', 'Pavia', 'Perugia', 'Pesaro Urbino', 'Pescara', 'Piacenza', 'Pisa', 'Pistoia', 'Pordenone', 'Potenza', 'Prato', 'Ragusa', 'Ravenna', 'Reggio Emilia', 'Rieti', 'Rimini', 'Rovigo', 'Salerno', 'Sassari', 'Savona', 'Siena', 'Siracusa', 'Sondrio', 'Taranto', 'Teramo', 'Terni', 'Trapani', 'Trento', 'Treviso', 'Trieste', 'Udine', 'Varese', 'Verbano-Cusio-Ossola', 'Vercelli', 'Verona', 'Vibo Valentia', 'Vicenza', 'Viterbo'],

  state_abbrs: ['AG', 'AL', 'AN', 'AO', 'AR', 'AP', 'AT', 'AV', 'BT', 'BL', 'BN', 'BG', 'BI', 'BZ', 'BS', 'BR', 'CL', 'CB', 'CE', 'CZ', 'CH', 'CO', 'CS', 'CR', 'KR', 'CN', 'EN', 'FM', 'FE', 'FG', 'FC', 'FR', 'GO', 'GR', 'IM', 'IS', 'SP', 'AQ', 'LT', 'LE', 'LC', 'LI', 'LO', 'LU', 'MC', 'MN', 'MS', 'MT', 'MO', 'MB', 'NO', 'NU', 'OR', 'PD', 'PR', 'PV', 'PG', 'PU', 'PE', 'PC', 'PI', 'PT', 'PN', 'PZ', 'PO', 'RG', 'RA', 'RE', 'RI', 'RN', 'RO', 'SA', 'SS', 'SV', 'SI', 'SR', 'SO', 'TA', 'TE', 'TR', 'TP', 'TN', 'TV', 'TS', 'UD', 'VA', 'VB', 'VC', 'VR', 'VV', 'VI', 'VT'],

  cities: ['Agrigento', 'Alessandria', 'Ancona', 'Aosta', 'Arezzo', 'Ascoli Piceno', 'Asti', 'Avellino', 'Barletta', 'Belluno', 'Benevento', 'Bergamo', 'Biella', 'Bolzano', 'Brescia', 'Brindisi', 'Caltanissetta', 'Campobasso', 'Caserta', 'Catanzaro', 'Chieti', 'Como', 'Cosenza', 'Cremona', 'Crotone', 'Cuneo', 'Enna', 'Fermo', 'Ferrara', 'Fidenza', 'Foggia', 'Fontanellato', 'Forlì', 'Frosinone', 'Gorizia', 'Grosseto', 'Imperia', 'Isernia', 'La Spezia', 'L\'Aquila', 'Latina', 'Lecce', 'Lecco', 'Livorno', 'Lodi', 'Lucca', 'Macerata', 'Mantova', 'Massa', 'Matera', 'Modena', 'Monza', 'Novara', 'Nuoro', 'Oristano', 'Padova', 'Parma', 'Pavia', 'Perugia', 'Pesaro', 'Pescara', 'Piacenza', 'Pisa', 'Pistoia', 'Pordenone', 'Potenza', 'Prato', 'Ragusa', 'Ravenna', 'Reggio Emilia', 'Rieti', 'Rimini', 'Rovigo', 'Salerno', 'Sassari', 'Savona', 'Siena', 'Siracusa', 'Sondrio', 'Taranto', 'Teramo', 'Terni', 'Trapani', 'Trento', 'Treviso', 'Trieste', 'Udine', 'Varese', 'Verbano', 'Vercelli', 'Verona', 'Vibo Valentia', 'Vicenza', 'Viterbo'],

  street_prefixes: ['Argine', 'Borgo', 'Calle', 'Campo', 'Canale', 'Contrada', 'Corso', 'Fondamenta', 'Frazione', 'Galleria', 'Largo', 'Passo', 'Piazza', 'Piazzale', 'Ripa', 'Rua', 'Strada', 'Traversa', 'Via', 'Viale', 'Vicolo'],

  street_suffixes:['7 Fratelli Cervi', 'Alessandro Volta', 'Alfieri', 'Bellini', 'Carducci', 'Cavour', 'Cesare Battisti', 'Como', 'Cristoforo Colombo', 'Dante Alighieri', 'Donizetti', 'Duca d\'Aosta', 'Enrico Fermi', 'Europa', 'Farini', 'Fiume', 'Foscolo', 'fratelli Cairoli', 'Galileo Galilei', 'Garibaldi', 'Giovanni XXII', 'Gorizia', 'Isonzo', 'Italia', 'IV Novembre', 'John Fitzgerald Kennedy', 'Leonardo Da Vinci', 'Leopardi', 'Manzoni', 'Marconi', 'Mascagni', 'Massimo d\'Azeglio', 'Matteotti', 'Mazzini', 'Michelangelo Buonarroti', 'Monte Grappa', 'Nazario Sauro', 'Nino Bixio', 'Pascoli', 'Petrarca', 'Puccini', 'Raffaello Sanzio', 'Risorgimento', 'Rossini', 'San Rocco', 'Sant\'Antonio', 'Silvio Pellico', 'Tasso', 'Ugo Bassi', 'Verdi', 'Vittorio Veneto', 'XXIV Maggio'],

  zip_formats: ['#####'],

  building_number_formats: ['##', '###'],

  street_formats: [
    '{{street_prefix}} {{street_suffix}}'
  ],

  address1_formats: [
    '{{street}}',
    '{{street}} {{address2}}'
  ],

  address2_formats: ['#', '##', '##/b'],

  address_formats: [
    '{{address1}}\n{{zip}} {{city}}',
    '{{address1}}\n{{zip}} {{city}}\n{{state_abbr}}',
    '{{address1}}\n{{zip}} {{city}}\n{{state}}',
  ],

  city: function() {
    return this.populate_one_of(this.cities);
  },

  state: function() {
    return this.populate_one_of(this.states);
  },

  street: function() {
    return this.populate_one_of(this.street_formats);
  },

  street_prefix: function() {
    return this.random_element(this.street_prefixes);
  },

};

module.exports = provider;
