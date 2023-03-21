var provider = {
  countries: ['Afghanistan', 'Afrique du Sud', 'Albanie', 'Algérie',
  'Allemagne', 'Andorre', 'Angola', 'Antigua-et-Barbuda', 'Arabie saoudite',
  'Argentine', 'Arménie', 'Australie', 'Autriche',
  'Azerbaïdjan', 'Bahamas', 'Bahreïn', 'Bangladesh', 'Barbade',
  'Belgique', 'Belize', 'Bénin', 'Bhoutan', 'Biélorussie', 'Myanmar',
  'Bolivie', 'Bosnie-Herzégovine', 'Botswana', 'Brésil', 'Brunei',
  'Bulgarie', 'Burkina Faso', 'Burundi', 'Cambodge', 'Cameroun',
  'Canada', 'Cap-Vert', 'Centrafrique', 'Chili',
  'République populaire de Chine', 'Chypre', 'Colombie', 'Comores',
  'Congo-Brazzaville', 'République démocratique du Congo', 'Corée du Nord',
  'Corée du Sud', 'Costa Rica', 'Côte d\'Ivoire', 'Croatie', 'Cuba', 'Danemark',
  'Djibouti', 'République dominicaine', 'Dominique', 'Égypte',
  'Émirats arabes unis', 'Équateur', 'Érythrée', 'Espagne', 'Estonie',
  'États-Unis', 'Éthiopie', 'Fidji', 'Finlande', 'France', 'Gabon', 'Gambie',
  'Géorgie', 'Ghana', 'Grèce', 'Grenade', 'Guatemala', 'Guinée',
  'Guinée-Bissau', 'Guinée équatoriale', 'Guyana', 'Haïti', 'Honduras',
  'Hongrie', 'Inde', 'Indonésie', 'Irak', 'Iran', 'Irlande', 'Islande',
  'Israël', 'Italie', 'Jamaïque', 'Japon', 'Jordanie', 'Kazakhstan',
  'Kenya', 'Kirghizistan', 'Kiribati', 'Koweït', 'Laos', 'Lesotho',
  'Lettonie', 'Liban', 'Libéria', 'Libye', 'Liechtenstein', 'Lituanie',
  'Luxembourg', 'Macédoine', 'Madagascar', 'Malaisie', 'Malawi',
  'Maldives', 'Mali', 'Malte', 'Maroc', 'Îles Marshall', 'Maurice',
  'Mauritanie', 'Mexique', 'Micronésie', 'Moldavie', 'Monaco',
  'Mongolie', 'Monténégro', 'Mozambique', 'Namibie', 'Nicaragua',
  'Niger', 'Nigeria', 'Niue', 'Norvège', 'Nouvelle-Zélande', 'Oman',
  'Ouganda', 'Ouzbékistan', 'Pakistan', 'Palaos', 'Palestine', 'Panamá',
  'Papouasie-Nouvelle-Guinée', 'Paraguay', 'Pays-Bas', 'Pérou',
  'Philippines', 'Pologne', 'Portugal', 'Qatar', 'Roumanie', 'Royaume-Uni',
  'Russie', 'Rwanda', 'Saint-Christophe-et-Niévès', 'Sainte-Lucie',
  'Saint-Marin', 'Saint-Vincent-et-les-Grenadines', 'Salomon', 'Salvador',
  'Samoa', 'São Tomé-et-Principe',
  'Sénégal', 'Serbie', 'Seychelles', 'Sierra Leone', 'Singapour',
  'Slovaquie', 'Slovénie', 'Somalie', 'Soudan', 'Sri Lanka', 'Suède',
  'Suisse', 'Suriname', 'Swaziland',
  'Syrie', 'Tadjikistan', 'Tanzanie', 'Tchad', 'République tchèque',
  'Thaïlande', 'Timor oriental', 'Togo', 'Tonga', 'Trinité-et-Tobago',
  'Tunisie', 'Turkménistan', 'Turquie', 'Tuvalu', 'Ukraine', 'Uruguay',
  'Vanuatu', 'Vatican', 'Venezuela', 'Viêt Nam', 'Yémen', 'Zambie',
  'Zimbabwe'],


  states: ['Auvergne-Rhône-Alpes', 'Bourgogne-Franche-Comté', 'Bretagne',
  'Centre-Val de Loire', 'Corse', 'Grand Est', 'Hauts-de-France',
  'Île-de-France', 'Normandie', 'Nouvelle-Aquitaine', 'Occitanie',
  'Pays de la Loire', 'Provence-Alpes-Côte d\'Azur', 'Guadeloupe',
  'Guyane', 'Martinique', 'La Réunion', 'Mayotte'],

  state_abbrs: ['ARA', 'BFC', 'BRE', 'CVL', 'COR', 'GES', 'HDF', 'IDF',
  'NOR', 'NAQ', 'OCC', 'PDL', 'PAC', 'GP', 'GF', 'MQ', 'RE', 'YT'],

  cities: ['Aix-en-Provence', 'Agen', 'Ajaccio', 'Amiens', 'Angers',
  'Avignon', 'Argenteuil', 'Auxerre', 'Basse-Terre', 'Bayonne',
  'Besançon', 'Bordeaux', 'Brest', 'Caen', 'Cannes', 'Cayenne',
  'Clermont-Ferrand', 'Colmar', 'Dijon', 'Dunkerque', 'Fort-de-France',
  'Grenoble', 'Montpellier', 'Le Havre', 'Le Mans',
  'Levallois-Perret', 'Lille', 'Limoges', 'Lyon', 'Marseille', 'Metz',
  'Nancy', 'Nantes', 'Nice', 'Nîmes', 'Orléans', 'Paris', 'Pau',
  'Perpignan', 'Poitiers', 'Reims', 'Rennes', 'Roubaix', 'Rouen',
  'Saint-Denis', 'Saint-Étienne', 'Strasbourg', 'Toulon', 'Toulouse',
  'Tours', 'Versaille', 'Villeurbanne'],

  street_prefixes: ['Allée', 'Avenue', 'Boulevard', 'Chemin', 'Cours',
  'Impasse', 'Passage', 'Place', 'Route', 'Rue'],

  street_suffixes: ['Albert Camus', 'Charles-de-Gaulle', 'Jean Moulin',
  'Marie Curie', 'Napoléon Bonaparte', 'St Exupéry', 'de Paris',
  'de la Gare', 'd\'Avignon', 'de la République', 'des Vieux Chênes',
  'du 8 mai 1945', 'du Levant', 'du Marché', 'du Moulin',
  'des Champs', 'du six juin', 'des combattants', 'du 112ème Régiment',
  'de l\'Église', 'de Belfort', 'des Nations', 'de l\'Hôtel-de-Ville'],

  zip_formats: ['####0', '###00'],

  building_number_formats: ['#', '##', '###'],

  street_formats: [
    '{{street_prefix}} {{street_suffix}}',
    '{{street_prefix}} {{first_name}} {{last_name}}'
  ],

  address1_formats: [
    'Bâtiment X',
    'Appartement ##',
  ],

  address2_formats: [
    '{{building_number}} {{street}}',
  ],

  address_formats: [
    '{{address1}}\n{{address2}}\n{{zip}} {{city}}',
    '{{address2}}\n{{zip}} {{city}}',
  ],

  zip: function() {
    return this.numerify(this.random_element(this.zip_formats));
  },

  address1: function() {
    return this.numerify(this.letterify(this.random_element(this.address1_formats)));
  },

  address2: function() {
    return this.populate_one_of(this.address2_formats);
  },

  address: function() {
    return this.numerify(this.populate_one_of(this.address_formats));
  },

  city: function() {
    return this.random_element(this.cities);
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
};

module.exports = provider;
