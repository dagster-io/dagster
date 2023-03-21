var glues = ['.', '-', '_', null];

var provider = {
	phone_formats: ['(##)#####-####'],

	prefix: ['Sr.', 'Sra.', 'Dr.', 'Dra'],

	suffix: ['Júnior.', 'Sobrinho.', 'I', 'II', 'III', 'IV', 'V', 'Filho', 'Neto'],

	company_suffixes: ['S/A', '& Cia', 'LLC', 'Group', '& Filhos', 'Ltd'],

	catch_phrase_words: [
		['Adaptive', 'Advanced', 'Ameliorated', 'Assimilated', 'Automated', 'Balanced', 'Business-focused', 'Centralized', 'Cloned', 'Compatible', 'Configurable', 'Cross-group', 'Cross-platform', 'Customer-focused', 'Customizable', 'Decentralized', 'De-engineered', 'Devolved', 'Digitized', 'Distributed', 'Diverse', 'Down-sized', 'Enhanced', 'Enterprise-wide', 'Ergonomic', 'Exclusive', 'Expanded', 'Extended', 'Facetoface', 'Focused', 'Front-line', 'Fully-configurable', 'Function-based', 'Fundamental', 'Future-proofed', 'Grass-roots', 'Horizontal', 'Implemented', 'Innovative', 'Integrated', 'Intuitive', 'Inverse', 'Managed', 'Mandatory', 'Monitored', 'Multi-channelled', 'Multi-lateral', 'Multi-layered', 'Multi-tiered', 'Networked', 'Object-based', 'Open-architected', 'Open-source', 'Operative', 'Optimized', 'Optional', 'Organic', 'Organized', 'Persevering', 'Persistent', 'Phased', 'Polarised', 'Pre-emptive', 'Proactive', 'Profit-focused', 'Profound', 'Programmable', 'Progressive', 'Public-key', 'Quality-focused', 'Reactive', 'Realigned', 'Re-contextualized', 'Re-engineered', 'Reduced', 'Reverse-engineered', 'Right-sized', 'Robust', 'Seamless', 'Secured', 'Self-enabling', 'Sharable', 'Stand-alone', 'Streamlined', 'Switchable', 'Synchronised', 'Synergistic', 'Synergized', 'Team-oriented', 'Total', 'Triple-buffered', 'Universal', 'Up-sized', 'Upgradable', 'User-centric', 'User-friendly', 'Versatile', 'Virtual', 'Visionary', 'Vision-oriented'],
		['24hour', '24/7', '3rdgeneration', '4thgeneration', '5thgeneration', '6thgeneration', 'actuating', 'analyzing', 'assymetric', 'asynchronous', 'attitude-oriented', 'background', 'bandwidth-monitored', 'bi-directional', 'bifurcated', 'bottom-line', 'clear-thinking', 'client-driven', 'client-server', 'coherent', 'cohesive', 'composite', 'context-sensitive', 'contextually-based', 'content-based', 'dedicated', 'demand-driven', 'didactic', 'directional', 'discrete', 'disintermediate', 'dynamic', 'eco-centric', 'empowering', 'encompassing', 'even-keeled', 'executive', 'explicit', 'exuding', 'fault-tolerant', 'foreground', 'fresh-thinking', 'full-range', 'global', 'grid-enabled', 'heuristic', 'high-level', 'holistic', 'homogeneous', 'human-resource', 'hybrid', 'impactful', 'incremental', 'intangible', 'interactive', 'intermediate', 'leadingedge', 'local', 'logistical', 'maximized', 'methodical', 'mission-critical', 'mobile', 'modular', 'motivating', 'multimedia', 'multi-state', 'multi-tasking', 'national', 'needs-based', 'neutral', 'nextgeneration', 'non-volatile', 'object-oriented', 'optimal', 'optimizing', 'radical', 'real-time', 'reciprocal', 'regional', 'responsive', 'scalable', 'secondary', 'solution-oriented', 'stable', 'static', 'systematic', 'systemic', 'system-worthy', 'tangible', 'tertiary', 'transitional', 'uniform', 'upward-trending', 'user-facing', 'value-added', 'web-enabled', 'well-modulated', 'zeroadministration', 'zerodefect', 'zerotolerance'],
		['ability', 'access', 'adapter', 'algorithm', 'alliance', 'analyzer', 'application', 'approach', 'architecture', 'archive', 'artificialintelligence', 'array', 'attitude', 'benchmark', 'budgetarymanagement', 'capability', 'capacity', 'challenge', 'circuit', 'collaboration', 'complexity', 'concept', 'conglomeration', 'contingency', 'core', 'customerloyalty', 'database', 'data-warehouse', 'definition', 'emulation', 'encoding', 'encryption', 'extranet', 'firmware', 'flexibility', 'focusgroup', 'forecast', 'frame', 'framework', 'function', 'functionalities', 'GraphicInterface', 'groupware', 'GraphicalUserInterface', 'hardware', 'help-desk', 'hierarchy', 'hub', 'implementation', 'info-mediaries', 'infrastructure', 'initiative', 'installation', 'instructionset', 'interface', 'internetsolution', 'intranet', 'knowledgeuser', 'knowledgebase', 'localareanetwork', 'leverage', 'matrices', 'matrix', 'methodology', 'middleware', 'migration', 'model', 'moderator', 'monitoring', 'moratorium', 'neural-net', 'openarchitecture', 'opensystem', 'orchestration', 'paradigm', 'parallelism', 'policy', 'portal', 'pricingstructure', 'processimprovement', 'product', 'productivity', 'project', 'projection', 'protocol', 'securedline', 'service-desk', 'software', 'solution', 'standardization', 'strategy', 'structure', 'success', 'superstructure', 'support', 'synergy', 'systemengine', 'task-force', 'throughput', 'time-frame', 'toolset', 'utilisation', 'website', 'workforce']
	],

	first_names: ['Aílton', 'Aaron', 'Abgail', 'Alessandro', 'Alan', 'Aline', 'Álvaro', 'Alberto', 'Amanda', 'Ana Carolina', 'Ana Carla', 'Andréia', 'Augusto', 'Abelardo', 'Angela', 'Antonio', 'Adriana', 'Aurélio',
				  'Alice', 'Bernardo', 'Bruno', 'Bruna', 'Bárbara', 'Caio', 'Camila', 'Carlos', 'Carla', 'Carmen', 'Carolina', 'Célia', 'Celso', 'Cristina', 'Christiane', 'Cícero', 'Cínthia', 'Clodoaldo',
				  'Daniela', 'Danielle', 'Danilo', 'Daniel', 'Daisy', 'Davi', 'Denise', 'Diego', 'Edilene', 'Eduardo', 'Elizabeth', 'Érica', 'Ester', 'Eva', 'Eduardo', 'Eduarda', 'Fabiana', 'Fábio',
				  'Flávia', 'Flávio', 'Felipe', 'Fernanda', 'Fernando', 'Francisco', 'Gustavo', 'Giulia', 'Giovanna', 'Gabriel', 'Gabriela', 'Gil', 'Graça', 'Hamilton', 'Heitor', 'Heloísa', 'Hugo', 'Igor',
				  'Isis', 'Ingrid', 'Ian', 'João', 'João Paulo', 'João Vítor', 'Joaquim', 'José', 'Joel', 'Jorge', 'Jaqueline', 'Joana', 'Joice', 'Judite', 'Júlia', 'Karen', 'Kátia', 'Kelly',
				  'Kevin', 'Laércio', 'Leandro', 'Leonardo', 'Leonel', 'Lucas', 'Luís', 'Luana', 'Luciana', 'Luíza', 'Laiza', 'Leona', 'Lucília', 'Lúcia', 'Lívia', 'Mariana', 'Manuela', 'Marcela', 'Magali',
				  'Maria', 'Mariza', 'Maysa', 'Mel', 'Michelle', 'Monica', 'Márcio', 'Manuel', 'Mário', 'Mauro', 'Miguel', 'Moisés', 'Nélio', 'Nicolas', 'Nádia', 'Nair', 'Nathália', 'Natasha', 'Olga', 'Olívia',
				  'Otávio', 'Orlando', 'Osmar', 'Paulo', 'Plínio', 'Pedro', 'Paloma', 'Paola', 'Priscila', 'Paula', 'Patrícia', 'Quitéria', 'Rafaela', 'Raquel', 'Rita', 'Renata', 'Rosa', 'Rebeca', 'Regina', 'Rafaela',
				  'Rafael', 'Reginaldo', 'Renato', 'Rodrigo', 'Rodolfo', 'Romulo', 'Rui', 'Sabrina', 'Sandra', 'Samira', 'Sandy', 'Samantha', 'Selma', 'Silvia', 'Sophia', 'Susana', 'Sandro', 'Saulo',
				  'Sérgio', 'Sidnei', 'Tadeu', 'Tiago', 'Túlio', 'Teodoro', 'Tatiana', 'Tainá', 'Talita', 'Teresa', 'Thaís', 'Úrsula', 'Ulisses', 'Valdemar', 'Valdir', 'Vicente', 'Victor', 'Valentina', 'Valéria',
				  'Vitória', 'Virgínia', 'Verônica', 'Wanda', 'Wilma', 'Wagner', 'Wilson', 'Xavier', 'Yasmin', 'Yuri', 'Zacarias', 'Zélia'],

	last_names: ['Abreu', 'Alves', 'Abshire', 'Adams', 'Almeida', 'Anderson', 'Araújo', 'Azevedo', 'Antunes' , 'Amaral' ,'Avelar', 'Abraão', 'Agrizzi', 'Alcântara', 'Alvarenga', 'Bailey', 'Barbosa', 'Brito', 'Bartell', 'Bartoletti', 'Barton', 'Baro', 'Barboza', 'Barcelos', 'Barone', 'Barros', 'Barroso', 'Batista', 'Blanco', 'Brunelli', 'Bernier', 'Bastos', 'Blanda', 'Beltrame', 'Bruen', 'Carroll', 'Carter', 'Calmon', 'Carvalho', 'Correia', 'Cabral', 'Calil', 'Carvalho', 'Casagrande', 'Cassini', 'Caprini', 'Carneiro', 'Carmo', 'Castro', 'Chagas', 'Conde', 'Costa', 'Costa', 'Cruz', 'Cahves', 'Cardoso', 'Cardozo', 'Daniel', 'de Fraga', 'da Silva', 'de ávila', 'de Oliveira', 'da Costa', 'de Araújo', 'de Matos', 'de Agnolli', 'de Andrade', 'de Assis', 'de Oliveira', 'Duarte', 'Donato', 'dos Santos', 'dos Reis', 'Durgan', 'Esteves', 'Esposito', 'Ernser', 'Ferreira', 'Fonseca', 'Faccin', 'Falsoni', 'Farias', 'Feitoza', 'Fraga', 'Ferrari', 'Flora', 'Freire', 'Freitas', 'Franecki', 'Friesen', 'Furtado', 'Guerra', 'Gago', 'Gava', 'Gazola', 'Gomes', 'Gonçalvez', 'Graça', 'Greco', 'Guimarães', 'Grassi', 'Gulgowski', 'Habib', 'Herman', 'Herculano', 'Henriques', 'Hoffman', 'Hammes', 'Hane', 'Hansen', 'Harris', 'Hartmann', 'Hill', 'Jacobi', 'Jacobs', 'Jacobson', 'Jesus', 'Jordão', 'Johnson', 'Johnston', 'Jones', 'Kassulke', 'Kautzer', 'Keebler', 'Keeling', 'Klein', 'Lage', 'Leite', 'Lans', 'Lago', 'Lanes', 'Lindgren', 'Larson', 'Leme', 'Lemos', 'Lessa', 'Loreto', 'Legros', 'Lopes', 'Lopez', 'Lourenço', 'Luca', 'Leal', 'Machado', 'Maggio', 'Mesquita', 'Macedo', 'Magaldi', 'Mafra', 'Marvin', 'Mayer', 'Malta', 'Mazzon', 'Matarazzo', 'Mello', 'Mendes', 'Mendonça', 'Moraes', 'Morais', 'Moreira', 'Matos', 'Malvezzi', 'Mills', 'Moore', 'Morissette', 'Muller', 'Nassar', 'Nicolas', 'Napoleão', 'Neves', 'Nitzsche', 'Nolan', 'Nascimento','Neto', 'Novaes', 'Nogueira', 'Nunes', 'Oliveira', 'Olsen', 'Olimpio', 'Pereira', 'Pacheco', 'Paes', 'Passos', 'Patrício', 'Pazeto', 'Pedrosa', 'Peixoto', 'Penha', 'Piccin', 'Powlowski', 'Prati', 'Prata', 'Prates', 'Peira', 'Quaresma', 'Queiroz', 'Rath', 'Rasmussen', 'Rodriguez', 'Rabelo', 'Ramos', 'Rangel', 'Raposo', 'Reis', 'Rigo', 'Rocha', 'Ribeiro', 'Rigone', 'Ritchie', 'Rodrigues', 'Rosas', 'Romaguera', 'Russel', 'Ryan', 'Salles', 'Santos', 'Sauer', 'Sawayn', 'Sá', 'Silva', 'Santiago', 'Santori', 'Sartóri', 'Schinner', 'Scharra', 'Schmidt', 'Simões', 'Schneider', 'Serafim', 'Schultz', 'Schumm', 'Shields', 'Simonis', 'Spencer', 'Stark', 'Strosin', 'Swift', 'Tozzi', 'Teves', 'Targa', 'Toledo', 'Thomaz', 'Tostes', 'Trindade', 'Tromp', 'Turcotte', 'Tomé', 'Ullrich', 'Upton', 'Vasconcelos', 'Viana', 'Vaccari', 'Valle', 'Vargas', 'Vaz', 'Villares', 'Vidal', 'Walsh', 'Waters', 'Watsica', 'Webber', 'West', 'White', 'Zardo', 'Zannete', 'Zanol' ],

	username_formats: [
		'{{last_name}}.{{first_name}}',
		'{{first_name}}.{{last_name}}',
		'{{first_name}}_{{last_name}}',
		'{{last_name}}_{{first_name}}'
	],

	name_formats: [
		'{{name_prefix}} {{full_name}}'
	],

	full_name_formats: [
		'{{first_name}} {{last_name}}'
	],

	company_name_formats: [
		'{{last_name}} {{company_suffix}}'
	],

	name: function() {
		return this.populate_one_of(this.name_formats);
	},

	username: function() {
		return this.populate_one_of(this.username_formats);
	},

	full_name: function() {
		return this.populate_one_of(this.full_name_formats);
	},

	first_name: function() {
		return this.random_element(this.first_names);
	},

	last_name: function() {
		return this.random_element(this.last_names);
	},

	password: function() {
		return this.numerify('#' + this.first_name + '##');
	},

	phone: function() {
		return this.numerify(this.random_element(this.phone_formats));
	},

	name_prefix: function() {
		return this.random_element(this.prefix);
	},

	name_suffix: function() {
		return this.random_element(this.suffix);
	},

	company_suffix: function() {
		return this.random_element(this.company_suffixes);
	},

	company_name: function() {
		return this.populate_one_of(this.company_name_formats);
	},

	catch_phrase: function() {
		var result = [];

		for (var i in this.catch_phrase_words) {
			result.push(this.random_element(this.catch_phrase_words[i]));
		}

        return result.join(' ');
	}
};

module.exports = provider;