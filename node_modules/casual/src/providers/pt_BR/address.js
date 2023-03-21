var provider = {
	city_prefixes: ['Norte', 'Leste', 'Oeste', 'Sul', 'Novo', 'Lago', 'Porto', 'Nova'],
	city_suffixes: [ 'lândia', 'polis', 'tuba' ],

	countries: ['Afeganistão', 'Albania', 'Argélia', 'Samoa Americana', 'Andorra', 'Angola', 'Antartida', 'Antigua e Barbuda', 'Argentina', 'Armenia', 'Aruba',
				'Austrália', 'Áustria', 'Azerbaijão', 'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados', 'Belarus',
				'Bélgica', 'Belize', 'Benin', 'Bermuda', 'Bhutão', 'Bolívia', 'Bósnia e Herzegovina', 'Botswana', 'Brasil', 'Ilhas Virgens Britânicas', 'Brunei', 'Bulgária',
				'Burkina Faso', 'Burundi', 'Camboja', 'Camarões', 'Canadá', 'Cabo Verde', 'Ilhas Cayman', 'República Centro-Africana', 'Chade', 'Chile', 'China',
				'Ilha Christmas', 'Colômbia', 'Comores', 'Congo', 'Ilhas Cook', 'Costa Rica', 'Costa do Marfim', 'Croácia', 'Cuba', 'Chipre', 'República Tcheca', 'Dinamarca',
				'Djibouti', 'Dominica', 'República Dominicana', 'Equador', 'Egito', 'El Salvador', ' Guinéa Equatorial', 'Eritréa', 'Estônia', 'Etiópia', 'Ilhas Faroe',
				'Ilhas Malvinas', 'Fiji', 'Finlândia', 'França', 'Guiana Francesa', 'Polinésia Francesa', 'Gabão', 'Gâmbia', 'Georgia', 'Alemanha', 'Gana', 'Gibraltar', 'Grécia',
				'Groelândia', 'Granada', 'Guam', 'Guatemala', 'Guernsey', 'Guiné', 'Guiné-Bissau', 'Guiana', 'Haiti', 'Vaticano', 'Honduras', 'Hong Kong', 'Hungria', 'Islândia',
				'Índia', 'Indonésia', 'Irã', 'Iraque', 'Irlanda', 'Israel', 'Itália', 'Jamaica', 'Japão', 'Jordânia', 'Cazaquistão', 'Quénia', 'Kiribati', 'Coréia do Norte', 'Coréia do Sul',
				'Kuwait', 'Quirguistão', 'Laos', 'Letônia', 'Lebanon', 'Líbano', 'Libéria', 'Líbia', 'Liechtenstein', 'Lituânia', 'Luxemburgo', 'Macau', 'Macedônia',
				'Madagáscar', 'Malawi', 'Malásia', 'Maldivas', 'Mali', 'Malta', 'Ilhas Marshall', 'Martinica', 'Mauritânia', 'Maurício', 'Mayotte', 'México', 'Micronésia',
				'Moldávia', 'Principado de Mônaco', 'Mongólia', 'Montenegro', 'Montserrat', 'Morrocos', 'Moçambique', 'Myanmar', 'Namíbia', 'Nauru', 'Nepal', 'Antilhas Holandesas', 'Holanda',
				'Nova Caledónia', 'Nova Zelândia', 'Nicarágua', 'Níger', 'Nigéria', 'Niue', 'Ilha Norfolk', 'Ilhas Marianas', 'Noruéga', 'Oman', 'Paquistão', 'Palau', 'Palestina', 'Panamá',
				'Papua Nova Guiné', 'Paraguai', 'Perú', 'Filipinas', 'Ilhas Picárnia', 'Polônia', 'Portugal', 'Porto Rico', 'Catar', 'Romênia', 'Federação Russa', 'Ruanda', 'São Bartolomeu',
				'Santa Helena', 'São Cristóvão e Nevis', 'Santa Lúcia', 'St Martin', 'Samoa', 'São Marino', 'São Tomé e Préncipe', 'Arábia Saudita', 'Senegal', 'Sérvia', 'Seicheles',
				'Serra Leoa', 'Singapura', 'Eslováquia', 'Eslovénia', 'Ilhas Salomão', 'Somália', 'África do Sul', 'Ilhas Geórgia do Sul e Sandwich do Sul', 'Espanha', 'Sri Lanka', 'Sudão',
				'Suriname', 'Suazilândia', 'Suécia', 'Suíça', 'Síria', 'Taiwan', 'Tajiquistão', 'Tanzânia', 'Tailândia', 'Timor-Leste', 'Togo', 'Tokelau', 'Tonga', 'Trinidad e Tobago',
				'Tunísia', 'Turquia', 'Turkmenistão', 'Ilhas Turcas e Caicos', 'Tuvalu', 'Uganda', 'Ucrânia', 'Emirados Árabes unidos', 'Reino Unido', 'Estados Unidos da América',
				'Ilhas Virgens Americanas', 'Uruguai', 'Uzbekistão', 'Vanuatu', 'Venezuela', 'Vietnam', 'Wallis e Futuna', 'Saara Ocidental', 'Iémen', 'Zâmbia', 'Zimbabwe'],

	zip_formats: ['#####-###'],

	street_prefixes: ['Beco', 'Avenida', 'Rua', 'Travessa', 'Rodovia', 'Ladeira', 'Alameda', 'Estrada' ],

	street_formats: [ '{{street_prefix}} {{real_street}}' ],

	//most common streets names
	streets: [
		'Principal', 'Sete', 'Brasil', 'Santo Antônio', 'Sete de Setembro', 'Quinze De Novembro', 'Castro Alves', 'Rui Barbosa', 'Da Paz', 'Miguel de Frias', 'Paulista', 'Cinco de Julho',
		'José Bonifácio', 'Dom Pedro II', 'Primeiro de Maio', 'Paulista', 'Flamengo', 'Santa Rita', 'Santos Dumont', 'Das Flores', 'Gonçalo de Carvalho', 'Contorno', 'Tabajaras', 'Caetés',
		'Almirante Tamandaré', 'Amaral Peixoto', 'Oscar Freire', 'Ayrton Senna', 'Castelo Branco', 'Fernão Dias', 'Bandeirantes', 'Do Mármore', 'Vieira Souto', 'Bartolomeu Mitre', 'Assembléia',
		'Amoroso Costa', 'Hilário de Gouveia', 'Tavares de Macêdo', 'Heitor Beltrão', 'José Higino', 'Mooca', 'Paes de Barros', 'Arthur Azevedo', 'Peixoto Gomide', 'Brigadeiro Luis Antônio',
		'Mario Amaral', 'Rebouças', 'Pinheiros', 'Itapirapuã', 'Gabriel Monteiro', 'Parque das Nações', 'Boaventura', 'Bacupã', 'Dr. Souza Gomes', 'Washington Luiz', 'Arantina', 'Parnaíba'
	],

	states: ['Acre', 'Alagoas', 'Amapá', 'Amazonas', 'Bahia', 'Ceará', 'Distrito Federal', 'Espírito Santo', 'Goiás', 'Maranhão', 'Mato Grosso', 'Mato Grosso do Sul', 'Minas Gerais', 'Pará',
			 'Paraíba', 'Paraná', 'Pernambuco', 'Piauí', 'Rio de Janeiro', 'Rio Grande do Norte', 'Rio Grande do Sul', 'Rondônia', 'Roraima', 'Santa Catarina', 'São Paulo', 'Sergipe', 'Tocantins'],

 	state_abbrs: ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'],

 	//state capitals and big cities
	cities: [ 'São Paulo', 'Rio de Janeiro', 'Salvador',
		'Brasília', 'Fortaleza', 'Belo Horizonte',
		'Capelle aan den IJssel', 'Castricum', 'Coevorden',
		'Manaus', 'Curitiba', 'Recife',
		'Porto Alegre', 'Belém', 'Goiânia',
		'Guarulhos', 'Campinas',
		'São Luís', 'São Gonçalo', 'Maceió',
		'Duque de Caxias', 'Natal', 'Campo Grande',
		'Teresina', 'São Bernardo do Campo',
		'Nova Iguaçu', 'João Pessoa', 'Santo André',
		'Osasco', 'São José dos Campos', 'Jaboatão dos Guararapes',
		'Ribeirão Preto', 'Uberlândia', 'Contagem',
		'Sorocaba', 'Aracaju', 'Feira de Santana',
		'Cuiabá', 'Joinville', 'Juiz de Fora',
		'Londrina', 'Aparecida de Goiânia', 'Ananindeua',
		'Niterói', 'Porto Velho', 'Campos dos Goytacazes',
		'Belford Roxo', 'Serra', 'Caxias do Sul',
		'Vila Velha', 'Florianópolis', 'São João de Meriti',
		'Mauá', 'Macapá', 'São José do Rio Preto',
		'Santos', 'Mogi das Cruzes', 'Betim',
		'Diadema', 'Campina Grande', 'Jundiaí',
		'Maringá', 'Montes Claros', 'Olinda',
		'Rio Branco', 'Anápolis', 'Vitória',
		'Pelotas', 'Petrolina', 'Blumenau' ],

	address_formats: [
		'{{address1}}\n{{city}}/{{state_abbr}} {{zip}}',
	],
	address1_formats: [
		'{{street}} {{building_number}}',
		'{{street}} {{building_number}} {{address2}}',
	],
	address2_formats: ['apt. ###'],

	street_prefix: function() {
		return this.random_element(this.street_prefixes);
	},

	city: function() {
		return this.random_element(this.cities);
	},

	street: function() {
		return this.populate_one_of(this.street_formats);
	},

	real_street: function() {
		return this.random_element(this.streets);
	},

	zip: function() {
		return this.numerify(this.random_element(this.zip_formats));
	}

}


module.exports = provider;