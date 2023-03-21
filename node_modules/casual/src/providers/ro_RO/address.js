var provider = {
	states: ['Alba', 'Arad', 'Argeş', 'Bacău', 'Bihor', 'Bistriţa-Năsăud', 'Botoşani', 'Brăila', 'Braşov', 'Buzău', 'Călăraşi', 'Caraş-Severin', 'Cluj', 'Constanţa',
		'Covasna', 'Dâmboviţa', 'Dolj', 'Galaţi', 'Giurgiu', 'Gorj', 'Harghita', 'Hunedoara', 'Ialomiţa', 'Iaşi', 'Ilfov', 'Maramureş', 'Mehedinţi', 'Mureş', 'Neamţ',
		'Olt', 'Prahova', 'Sălaj', 'Satu Mare', 'Sibiu', 'Suceava', 'Teleorman', 'Timiş', 'Tulcea', 'Vâlcea', 'Vaslui', 'Vrancea', 'Bucureşti'],

	state_abbrs: ['AB', 'AR', 'AG', 'BC', 'BH', 'BN', 'BT', 'BR', 'BV', 'BZ', 'CL', 'CS', 'CJ', 'CT', 'CV', 'DB', 'DJ', 'GL', 'GR', 'GJ', 'HR', 'HD', 'IL', 'IS', 'IF', 'MM', 'MH', 'MS', 'NT', 'OT', 'PH', 'SJ', 'SM', 'SB', 'SV', 'TR', 'TM', 'TL', 'VL', 'VS', 'VN', 'B'],

	cities: ['Bucureşti', 'Iaşi', 'Cluj-Napoca', 'Timişoara', 'Constanţa', 'Craiova', 'Galaţi', 'Braşov', 'Ploieşti', 'Brăila', 'Oradea', 'Bacău', 'Arad', 'Piteşti', 'Sibiu', 'Târgu Mureş', 'Baia Mare', 'Buzău', 'Satu Mare', 'Botoşani', 'Râmnicu Vâlcea', 'Suceava', 'Piatra Neamţ', 'Drobeta-Turnu Severin', 'Focşani', 'Târgu Jiu', 'Tulcea',
		'Târgovişte', 'Reşiţa', 'Bistriţa', 'Slatina', 'Hunedoara', 'Călăraşi', 'Vaslui', 'Giurgiu', 'Roman', 'Deva', 'Bârlad', 'Alba Iulia', 'Zalău', 'Sfântu Gheorghe', 'Turda', 'Mediaş', 'Slobozia', 'Oneşti', 'Alexandria', 'Petroşani', 'Lugoj', 'Medgidia', 'Paşcani', 'Tecuci', 'Miercurea Ciuc', 'Sighetu Marmaţiei', 'Mangalia',
		'Râmnicu Sărat', 'Câmpina', 'Dej', 'Câmpulung', 'Odorheiu Secuiesc', 'Reghin', 'Făgăraş', 'Caracal', 'Feteşti', 'Curtea de Argeş', 'Sighişoara', 'Roşiorii de Vede', 'Dorohoi', 'Turnu Măgurele', 'Fălticeni', 'Huşi', 'Vulcan', 'Rădăuţi', 'Olteniţa', 'Lupeni', 'Caransebeş', 'Săcele', 'Câmpia Turzii', 'Târnăveni', 'Sebeş', 'Aiud',
		'Motru', 'Carei', 'Moineşti', 'Codlea', 'Orăştie', 'Gherla', 'Moreni', 'Drăgăşani', 'Târgu Secuiesc', 'Băileşti', 'Câmpulung Moldovenesc', 'Blaj', 'Gheorgheni', 'Calafat', 'Adjud', 'Salonta', 'Urziceni', 'Marghita', 'Brad', 'Vatra Dornei', 'Topliţa', 'Orşova', 'Beiuş'],

	street_prefixes: ['Strada', 'Str.', 'Bulevardul', 'Bd.', 'Calea', 'Fundătura', 'Aleea', 'Piața', 'Intrarea', 'Șoseaua'],

	street_suffixes: ['Alexandru', 'Băiculești', 'Făurei', 'Hrisovului', 'Mateloților', 'Pajurei', 'Priporului', 'Privighetorilor', 'Oteșani', 'Pantelimon', 'Piatra Mare', 'Romula', 'Sargetia', 'Siliștea', 'Sinaia', 'Socului', 'Sucidava', 'Teiul Doamnei',
		'Tibiscum', 'Vergului', 'Zarandului', 'Cioplea', 'Ciucea', 'Florin Ciungan', 'Codrii Neamțului', 'Fetești', 'Fizicienilor', 'Foișorului', 'Fuiorului', 'Onisifor Ghibu', 'Giurgeni', 'Vasile Goldiș', 'Iosif Hodoș', 'Ianca', 'Ilioara', 'Jieneasca', 'Laceni', 'Lăcrămioarei',
		'Leorda', 'Lipănești', 'Lunca Bradului', 'Lunca Moldovei', 'Lunca Mureșului', 'Mădărași', 'Mănăstirea Agapia', 'Mizil', 'Moreni', 'Secuilor', 'Slătioara', 'Someșul Cald', 'Someșul Mare', 'Someșul Mic', 'Stupilor', 'Suter', 'Țebea', 'Terasei', 'Tohani', 'Tomești', 'Trestiana', 'Ucea', 'Uioara', 'Constantin Brâncoveanu',
		'Dimitrie Cantemir', 'Colectorului', 'George Coșbuc, poet', 'Libertății', 'Mărășești', 'Metalurgiei', 'Alexandru Obregia', 'Regina Maria', 'Gheorghe Șincai', 'Tineretului', 'Eroilor', 'Mihail Kogălniceanu', 'Libertății', 'Gheorghe Gh. Marinescu', 'Națiunile Unite', 'Regina Elisabeta', 'Schitu Măgureanu', 'Unirii', 'Tudor Vladimirescu', 'Constructorilor',
		'Geniului', 'Ghencea', 'Iuliu Maniu', 'Regiei', 'Timișoara', 'Vasile Milea', 'Chișinău', 'Dacia', 'Ferdinand I', 'Ghica Tei', 'Lacul Tei', 'Pierre de Coubertin', 'Dimitrie Pompeiu', 'Basarabia', 'Ion C. Brătianu', 'Burebista', 'Camil Ressu', 'Carol I', 'Corneliu Coposu', 'Decebal', 'Energeticienilor', 'Octavian Goga', 'Nicolae Grigorescu', 'Hristo Botev',
		'Mircea Vodă', 'Theodor Pallady', 'Râmnicu Sărat', 'Regina Elisabeta'],

	zip_formats: ['#####'],

	street_formats: [
		'{{street_prefix}} {{street_suffix}}'
	],

	address1_formats: [
		'{{street}} {{building_number}}'
	],

	address_formats: [
		'{{address1}}\n {{zip}} {{city}}, {{state}}',
	],

	city: function () {
		return this.random_element(this.cities);
	},

	state: function () {
		return this.populate_one_of(this.states);
	},

	street: function () {
		return this.populate_one_of(this.street_formats);
	},

	building_number: function () {
		return this.integer(1,200);
	},

	street_prefix: function () {
		return this.random_element(this.street_prefixes);
	},
};

module.exports = provider;
