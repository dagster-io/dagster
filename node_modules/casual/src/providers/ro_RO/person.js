var provider = {

	prefix: ['Dl.', 'Dna.', 'Dra.', 'Dr.', 'Prof. Dr.', 'Ing.'],

	company_suffixes: ['SA', 'SRL', 'PFA'],

	catch_phrase_words: [
		['Adaptive', 'Avansat', 'Ameliorat', 'Asimilate', 'Automatizat', 'Echilibrat', 'Concentrat de afaceri', 'Centralizat de', 'Clonat', 'Compatibil', 'Configurabil', 'Cros-grup', 'Traversare-platformă', 'Orientată spre client', 'Personalizabile', 'Descentralizate', 'Inginerie', 'Delegate', 'Digitalizat', 'Distribuit', 'Divers', 'Dimensiuni de jos', 'Îmbunătăţită', 'Nivel de întreprindere', 'Ergonomice', 'Exclusiv', 'Extins', 'Extins', 'Față în față', 'Concentrat', 'Prima linie', 'Complet configurabil', 'Bazate pe funcţie', 'Fundamentale', 'De viitor', 'De bază', 'Orizontale', 'Pus în aplicare', 'Inovatoare', 'Integrat', 'Intuitiv', 'Inversa', 'Gestionate', 'Obligatorii', 'Monitorizate', 'Multi-canalizat', 'Multi-laterale', 'Multi-strat', 'Mai multe niveluri', 'În reţea', 'Bazate pe obiect', 'Proiectat de deschidere', 'Open-source', 'Faptul generator', 'Optimizat', 'Opţional', 'Organice', 'Organizat', 'Perseverent', 'Persistente', 'Eliminate', 'Polarizate', 'Drept de preempţiune', 'Proactivă', 'Concentrat de profit', 'Profund', 'Programabile', 'Progresivă', 'Cheie publică', 'Concentrat de calitate', 'Reactive', 'Realiniat', 'Re-contextualizată', 'Re-industriale', 'Redus', 'Inginerie inversă', 'Dreptul de dimensiuni', 'Robustă', 'Fără sudură', 'Asigurat', 'Auto-care să permită', 'Poate fi partajat', 'Stand-alone', 'Simplificat', 'Comutare', 'Sincronizate', 'Sinergice', 'Synergizat', 'Echipa-orientate spre', 'Total', 'Triple-buffered', 'Universal', 'Dimensiuni de sus', 'Upgradabil', 'Utilizator-centrice', 'Uşor de utilizat', 'Versatil', 'Virtual', 'Vizionar', 'Viziune-orientate spre'],
		['24 de ore', '24/7', '3rdgeneration', '4thgeneration', '5thgeneration', '6thgeneration', 'actionare', 'analiza', 'asimetric', 'asincron', 'atitudine orientată', 'fundal', 'monitorizate de lăţime de bandă', 'bi-directionala', 'bifurcat', 'line de jos', 'clar-gândire', 'bazate pe client', 'client-server', 'coerent', 'coeziune', 'compozit', 'contact-sensitive', 'contextual bazate', 'pe bază de conţinut', 'dedicat', 'bazate pe cerere', 'didactice', 'direcţională', 'discret', 'disintermediate', 'dinamic', 'Eco-centrice', 'responsabilizarea', 'care să cuprindă', 'bine bazate', 'executiv', 'explicite', 'îl secretă', 'tolerante', 'prim-plan', 'proaspete de gândire', 'gama completa', 'la nivel mondial', 'grila-activat', 'euristică', 'la nivel înalt', 'holistică', 'omogen', 'resurse umane', 'hibrid', 'impact', 'elementare', 'necorporale', 'interactiv', 'intermediar', 'ultimul răcnet', 'locale', 'logistice', 'maximizat', 'metodice', 'critice', 'mobil', 'modulare', 'motivarea', 'multimedia', 'multi-stat', 'multi-tasking', 'naţionale', 'bazate pe nevoile', 'neutru', 'NextGeneration', 'nevolatile', 'orientat pe obiect', 'optim', 'optimizarea', 'radicală', 'în timp real', 'reciproce', 'regionale', 'receptiv', 'scalabile', 'secundar', 'orientate pe solutie', 'stabil', 'statice', 'sistematică', 'sistemice', 'per sistem', 'corporale', 'terţiar', 'tranzitorii', 'uniforme', 'trend ascendent', 'orientate spre utilizator', 'valoare adăugată', 'bazat pe web', 'bine modulat', 'zeroadministration', 'zerodefect', 'zerotolerance'],
		['capacitatea de', 'acces', 'adaptor', 'Algoritmul', 'Alianţa', 'analizor', 'cerere', 'abordare', 'arhitectura', 'Arhiva', 'inteligență artificială', 'matrice', 'atitudinea', 'Benchmark-uri', 'management bugete', 'capacitatea de', 'capacitate', 'provocare', 'circuit', 'colaborare', 'complexitatea', 'Conceptul', 'conglomerat', 'de urgenţă', 'Core', 'loialitate clienți', 'baza de date', 'depozit de date', 'definiţia', 'emulare', 'codificarea', 'criptare', 'extranet', 'firmware-ul', 'flexibilitate', 'focusgroup', 'Prognoza', 'cadru', 'cadru', 'funcţia', 'functionalitati', 'GraphicInterface', 'Groupware', 'GraphicalUserInterface', 'hardware-ul', 'birou de ajutor', 'ierarhie', 'hub-ul', 'punerea în aplicare', 'info-mediaries', 'infrastructura', 'Iniţiativa', 'instalare', 'instructionset', 'interfata', 'internet', 'intranet', 'knowledgeuser', 'baza de cunostinte', 'localareanetwork', 'efectul de levier', 'matrici', 'Matrix', 'metodologia', 'middleware', 'migraţia', 'modelul', 'Moderator', 'monitorizare', 'moratoriu', 'nete neuronale', 'arhitectură deschisă', 'opensystem', 'orchestratie', 'paradigmă', 'paralelism', 'Politica', 'Portal', 'structura de preâ', 'îmbunătățire procese', 'produs', 'productivitate', 'proiect', 'proiecţie', 'Protocolul', 'securedline', 'birou de servicii', 'software-ul', 'soluţie', 'standardizare', 'Strategia', 'structura', 'succesul', 'suprastructură', 'suport', 'Sinergia', 'motor sistem', 'Task-force', 'un debit', 'interval de timp', 'set de instrumente', 'utilizarea', 'site-ul', 'forţa de muncă']
	],

// source http://www.name-statistics.org/ro/prenumecomune.php
	first_names: ['Adina', 'Adrian', 'Adriana', 'Alexandra', 'Alexandra Elena', 'Alexandra Ioana', 'Alexandra Maria', 'Alexandru', 'Alexandru Cristian', 'Alexandru Ionuț', 'Alexandru Mihai',
	'Alin', 'Alina', 'Alina Elena', 'Alina Maria', 'Alina Mihaela', 'Ana', 'Ana Maria', 'Anamaria', 'Anca', 'Anca Elena', 'Anca Maria', 'Ancuța',
	'Andra', 'Andrea', 'Andreea', 'Andreea Cristina', 'Andreea Elena', 'Andreea Ioana', 'Andreea Maria', 'Andreea Mihaela', 'Andrei',
	'Angela', 'Aurel', 'Aurelia', 'Bianca', 'Bogdan', 'Bogdan Alexandru', 'Bogdan Ionuț', 'Brândușa', 'Camelia', 'Carmen', 'Cătălin', 'Cătălina', 'Ciprian', 'Claudia',
	'Claudiu', 'Constantin', 'Corina', 'Cornel', 'Cornelia', 'Cosmin', 'Costel', 'Cristian', 'Cristina', 'Cristina Elena', 'Cristina Maria', 'Dan',
	'Daniel', 'Daniela', 'Dănuț', 'Diana', 'Diana Maria', 'Dorin', 'Dorina', 'Dragoș', 'Dumitru', 'Elena', 'Elena Alina',
	'Elena Andreea', 'Elena Cristina', 'Elena Daniela', 'Elena Roxana', 'Emil', 'Emilia', 'Eugen', 'Florentina', 'Florian', 'Florin', 'Florina', 'Gabriel',
	'Gabriela', 'George', 'Georgeta', 'Georgian', 'Georgiana', 'Gheorghe', 'Ileana', 'Ilie', 'Ioan', 'Ioana', 'Ioana Alexandra', 'Ioana Cristina', 'Ioana Maria', 'Ion',
	'Ionel', 'Ionela', 'Ionuț', 'Ionut Alexandru', 'Ionuț Cătălin', 'Ionuț Daniel', 'Irina', 'Iulia', 'Iulian', 'Iuliana', 'Laura', 'Laurențiu',
	'Lavinia', 'Liliana', 'Liviu', 'Loredana', 'Lucian', 'Luminița', 'Mădălina', 'Maria', 'Maria Alexandra', 'Maria Cristina', 'Maria Magdalena', 'Marian', 'Mariana', 'Marinela', 'Marius', 'Marius Ionuț',
	'Melinda', 'Mihaela', 'Mihai', 'Mihai Alexandru', 'Mihail', 'Mircea', 'Mirela', 'Monica', 'Nicolae', 'Nicoleta', 'Nicușor', 'Oana',
	'Oana Maria', 'Octavian', 'Ovidiu', 'Paul', 'Paula', 'Petrică', 'Petronela', 'Petru', 'Radu', 'Raluca', 'Raluca Elena', 'Ramona', 'Răzvan', 'Robert',
	'Rodica', 'Roxana', 'Roxana Elena', 'Roxana Maria', 'Sebastian', 'Sergiu', 'Silvia', 'Silviu', 'Simona', 'Sorin', 'Ștefan', 'Ștefania', 'Teodora', 'Tudor',
	'Valentin', 'Valentina', 'Vasile', 'Veronica', 'Victor', 'Violeta', 'Viorel', 'Viorica', 'Vlad'],

	// source: http://www.name-statistics.org/ro/numedefamiliecomune.php
	last_names: ['Adam', 'Albu', 'Aldea', 'Alexandru', 'Alexe', 'Andrei', 'Anghel', 'Anton', 'Apostol', 'Ardelean',
	'Avram', 'Baciu', 'Badea', 'Bălan', 'Balint', 'Banu', 'Barbu', 'Bejan', 'Blaga',
	'Boboc', 'Bogdan', 'Bota', 'Bratu', 'Bucur', 'Burlacu', 'Călin', 'Cătană', 'Cazacu',
	'Chiriac', 'Chirilă', 'Chiriță', 'Chiș', 'Chivu', 'Ciobanu', 'Ciocan', 'Cîrstea', 'Ciucă', 'Cojocaru', 'Coman', 'Constantin',
	'Constantinescu', 'Cornea', 'Cosma', 'Costache', 'Costea', 'Costin', 'Cozma', 'Crăciun', 'Crețu', 'Crișan', 'Cristea',
	'Croitoru', 'Cucu', 'Damian', 'Dan', 'Danciu', 'Dănilă', 'Dascălu', 'David', 'Diaconescu', 'Diaconu',
	'Dima', 'Dincă', 'Dinu', 'Dobre', 'Dogaru', 'Drăgan', 'Drăghici', 'Drăgoi', 'Dragomir', 'Dumitrache', 'Dumitrașcu', 'Dumitrescu',
	'Dumitru', 'Duță', 'Enache', 'Ene', 'Epure', 'Fărcaș', 'Filip', 'Florea', 'Florescu', 'Gal',
	'Gavrilă', 'Georgescu', 'Gheorghe', 'Gheorghiță', 'Gheorghiu', 'Gherman', 'Ghiță', 'Grecu', 'Grigoraș', 'Grigore',
	'Grosu', 'Groza', 'Iacob', 'Iancu', 'Ichim', 'Ignat', 'Ilie', 'Iliescu', 'Ion',
	'Ionescu', 'Ioniță', 'Iordache', 'Irimia', 'Ispas', 'Istrate', 'Ivan', 'Lazăr', 'Luca', 'Lungu',
	'Lupu', 'Macovei', 'Maftei', 'Manea', 'Manolache', 'Manole', 'Marcu', 'Mărginean', 'Marian', 'Marin', 'Marinescu', 'Martin',
	'Matei', 'Maxim', 'Micu', 'Mihai', 'Mihăilă', 'Mihalache', 'Mihalcea', 'Militaru', 'Mircea', 'Mirea', 'Miron', 'Miu',
	'Mocanu', 'Moise', 'Moldovan', 'Moldoveanu', 'Molnar', 'Morar', 'Moraru', 'Muntean', 'Munteanu', 'Mureșan',
	'Mușat', 'Năstase', 'Neacșu', 'Neagoe', 'Neagu', 'Nechita', 'Necula', 'Nedelcu', 'Negoiță',
	'Negrea', 'Negru', 'Nica', 'Nicolae', 'Niculae', 'Niculescu', 'Nistor', 'Niță', 'Nițu', 'Oancea',
	'Olariu', 'Olaru', 'Oltean', 'Olteanu', 'Oprea', 'Păduraru', 'Pană', 'Panait', 'Paraschiv', 'Pasca',
	'Pascu', 'Pătrașcu', 'Pătru', 'Păun', 'Pavel', 'Petcu', 'Petre', 'Petrescu', 'Pintilie', 'Pîrvu', 'Pop', 'Popa',
	'Popescu', 'Popovici', 'Preda', 'Prodan', 'Puiu', 'Radu', 'Rădulescu', 'Roman', 'Roșca', 'Roșu', 'Rotaru',
	'Rus', 'Rusu', 'Sabău', 'Șandor', 'Sandu', 'Sava', 'Savu', 'Șerban', 'Sima', 'Simion', 'Simon', 'Sîrbu', 'Soare',
	'Staicu', 'Stan', 'Stanciu', 'Stancu', 'Stănescu', 'Ștefan', 'Ștefănescu', 'Stoian', 'Stoica', 'Stroe', 'Suciu',
	'Tamaș', 'Tănasă', 'Tănase', 'Tătaru', 'Teodorescu', 'Toader', 'Toma', 'Tomescu', 'Trandafir', 'Trif', 'Trifan',
	'Tudor', 'Tudorache', 'Tudose', 'Turcu', 'Ungureanu', 'Ursu', 'Văduva', 'Varga', 'Vasile', 'Vasilescu', 'Vintilă', 'Vișan',
	'Vlad', 'Voicu', 'Voinea', 'Zaharia', 'Zamfir'],

	company_names: ['Com - G.M.G.', 'Donatelo', 'Ser & Ban S.C.C.', 'Zerma International', 'Maestro Media', 'Altry - Monde Consulting', 'Alcores International 2007', 'Ef-Concepts Prestigious Marketing', 'Ecopower Construct', 'Pecun Construct', 'Guiarte 2008', 'Granasal 2007', 'Star Faleza House', 'Ambalux', 'Callcenteronline.Com', 'Alba Dacia Invest', 'Dumaris Exchange', 'General Montaj Csicsari', 'Andrăşescu Company', 'Westbau Montage', 'Mocuta Serv', 'Aleu Imperium', 'Metal Arrows', 'Andromar', 'Tailor Comerţ', 'Luminanov', 'Netzach', 'Trebau Roberto', 'Fraker', 'Dr. Kollar Coaching Centre', 'Fortrend Gifts', 'Ajkarel Trade', 'Kevmex Trade', 'Unio Global Work', 'Dublino Horeca', 'Varad Trade', 'Merkol Oil', 'Internaţional Data Entry', 'Szendi Metal', 'Romvest Contact', 'White Vessel', 'Basilicus Construct', 'Neo Alchem Trade', 'Neorom Trade', 'Dobantrak', 'Voiculeana Cat', 'Double C Quality', 'Fram Impex', 'Airkab Serv', 'Sly Invest', 'Westbuild', 'Lug & Aln', 'Drynet Trading', 'Lorinel', 'Sport Mix 2010', 'Dn Star', 'Naukra', 'Mms Tivo Invest', 'Union Contact', 'Reality Center', 'Trusendi Ro', 'Szirovitza M Art', 'S.E.F.O.P.', 'Ruth Company', 'Cat-Flo-Imo', 'Direct Trading Zona 41 2012', 'Group Vanzari Expres'],

	// source: ../fr_FR ;-)
	username_formats: [
		'X{{last_name}}',
		'{{first_name}}.{{last_name}}',
		'{{first_name}}{{last_name}}',
		'{{last_name}}_{{first_name}}',
	],

	company_name: function () {
		return this.random_element(this.company_names);
	},

	username: function () {
		return this.letterify(
			this.populate_one_of(this.username_formats)
			// removing diacritics, special characters and lowercasing
			).normalize('NFD').replace(/\W/g, "").toLowerCase();
	},

	catch_phrase: function () {
		var result = [];

		for (var i in this.catch_phrase_words) {
			result.push(this.random_element(this.catch_phrase_words[i]));
		}

		return result.join(' ');
	}

};

module.exports = provider;
