var glues = ['.', '-', '_', null];

var provider = {
	phone_formats: ['##-####-####'],

	prefix: ['様'],

	suffix: ['Jr.', 'Sr.', 'I', 'II', 'III', 'IV', 'V', 'MD', 'DDS', 'PhD', 'DVM'],

	company_suffixes: ['株式会社', '有限会社', '合同会社', '（株）'],

	catch_phrase_words: [
		['Adaptive', 'Advanced', 'Ameliorated', 'Assimilated', 'Automated', 'Balanced', 'Business-focused', 'Centralized', 'Cloned', 'Compatible', 'Configurable', 'Cross-group', 'Cross-platform', 'Customer-focused', 'Customizable', 'Decentralized', 'De-engineered', 'Devolved', 'Digitized', 'Distributed', 'Diverse', 'Down-sized', 'Enhanced', 'Enterprise-wide', 'Ergonomic', 'Exclusive', 'Expanded', 'Extended', 'Facetoface', 'Focused', 'Front-line', 'Fully-configurable', 'Function-based', 'Fundamental', 'Future-proofed', 'Grass-roots', 'Horizontal', 'Implemented', 'Innovative', 'Integrated', 'Intuitive', 'Inverse', 'Managed', 'Mandatory', 'Monitored', 'Multi-channelled', 'Multi-lateral', 'Multi-layered', 'Multi-tiered', 'Networked', 'Object-based', 'Open-architected', 'Open-source', 'Operative', 'Optimized', 'Optional', 'Organic', 'Organized', 'Persevering', 'Persistent', 'Phased', 'Polarised', 'Pre-emptive', 'Proactive', 'Profit-focused', 'Profound', 'Programmable', 'Progressive', 'Public-key', 'Quality-focused', 'Reactive', 'Realigned', 'Re-contextualized', 'Re-engineered', 'Reduced', 'Reverse-engineered', 'Right-sized', 'Robust', 'Seamless', 'Secured', 'Self-enabling', 'Sharable', 'Stand-alone', 'Streamlined', 'Switchable', 'Synchronised', 'Synergistic', 'Synergized', 'Team-oriented', 'Total', 'Triple-buffered', 'Universal', 'Up-sized', 'Upgradable', 'User-centric', 'User-friendly', 'Versatile', 'Virtual', 'Visionary', 'Vision-oriented'],
		['24hour', '24/7', '3rdgeneration', '4thgeneration', '5thgeneration', '6thgeneration', 'actuating', 'analyzing', 'assymetric', 'asynchronous', 'attitude-oriented', 'background', 'bandwidth-monitored', 'bi-directional', 'bifurcated', 'bottom-line', 'clear-thinking', 'client-driven', 'client-server', 'coherent', 'cohesive', 'composite', 'context-sensitive', 'contextually-based', 'content-based', 'dedicated', 'demand-driven', 'didactic', 'directional', 'discrete', 'disintermediate', 'dynamic', 'eco-centric', 'empowering', 'encompassing', 'even-keeled', 'executive', 'explicit', 'exuding', 'fault-tolerant', 'foreground', 'fresh-thinking', 'full-range', 'global', 'grid-enabled', 'heuristic', 'high-level', 'holistic', 'homogeneous', 'human-resource', 'hybrid', 'impactful', 'incremental', 'intangible', 'interactive', 'intermediate', 'leadingedge', 'local', 'logistical', 'maximized', 'methodical', 'mission-critical', 'mobile', 'modular', 'motivating', 'multimedia', 'multi-state', 'multi-tasking', 'national', 'needs-based', 'neutral', 'nextgeneration', 'non-volatile', 'object-oriented', 'optimal', 'optimizing', 'radical', 'real-time', 'reciprocal', 'regional', 'responsive', 'scalable', 'secondary', 'solution-oriented', 'stable', 'static', 'systematic', 'systemic', 'system-worthy', 'tangible', 'tertiary', 'transitional', 'uniform', 'upward-trending', 'user-facing', 'value-added', 'web-enabled', 'well-modulated', 'zeroadministration', 'zerodefect', 'zerotolerance'],
		['ability', 'access', 'adapter', 'algorithm', 'alliance', 'analyzer', 'application', 'approach', 'architecture', 'archive', 'artificialintelligence', 'array', 'attitude', 'benchmark', 'budgetarymanagement', 'capability', 'capacity', 'challenge', 'circuit', 'collaboration', 'complexity', 'concept', 'conglomeration', 'contingency', 'core', 'customerloyalty', 'database', 'data-warehouse', 'definition', 'emulation', 'encoding', 'encryption', 'extranet', 'firmware', 'flexibility', 'focusgroup', 'forecast', 'frame', 'framework', 'function', 'functionalities', 'GraphicInterface', 'groupware', 'GraphicalUserInterface', 'hardware', 'help-desk', 'hierarchy', 'hub', 'implementation', 'info-mediaries', 'infrastructure', 'initiative', 'installation', 'instructionset', 'interface', 'internetsolution', 'intranet', 'knowledgeuser', 'knowledgebase', 'localareanetwork', 'leverage', 'matrices', 'matrix', 'methodology', 'middleware', 'migration', 'model', 'moderator', 'monitoring', 'moratorium', 'neural-net', 'openarchitecture', 'opensystem', 'orchestration', 'paradigm', 'parallelism', 'policy', 'portal', 'pricingstructure', 'processimprovement', 'product', 'productivity', 'project', 'projection', 'protocol', 'securedline', 'service-desk', 'software', 'solution', 'standardization', 'strategy', 'structure', 'success', 'superstructure', 'support', 'synergy', 'systemengine', 'task-force', 'throughput', 'time-frame', 'toolset', 'utilisation', 'website', 'workforce']
	],

	first_names: ['恵子', '菜々美', '智', '真一', '京子', '博之', '三郎', '薫', '夏希', '三郎', '寿明', '圭', '弘也', '涼', '佳乃', '涼音', 'みあ', '薫', '悟志', 'はるみ', 'ミヤ', '寿々花', '恵梨香', '明', '寛治', 'さやか', '由樹', '拓郎', 'ケンイチ', '貴美子', '菜々美', '正義', '亮', '博之', '杏', '育子', '栄一', '勝久', '幸平', '知世', '隆太', '璃子', '将也', '亜希', '真一', '美紀', '遥', '美和子', '玲那', 'はじめ', '芳正', '綾女', '昌代', 'サダヲ', '秀樹', '獅童', '晃司', 'はるか', 'しぼり', '了', 'ヒロ', '陽子', '千佳子', '信吾', 'まなみ', '怜奈', '菊生', '有起哉', '秀隆', '達士', '博之', '建', '昴', '淳', 'まみ', '守', '理紗', '明', '淳', '秀隆', '恵望子', '友也', '未華子', '浩介', '菊生', '功補', '景子', '恭子', '禄郎', '菜摘', '美菜', '愛子', '惇', '里穂', '光臣', '佐知子', '隆之介', '将也', '俊二', '右京' ],

	last_names: ['寺脇', '西脇', '大泉', '春日', '玉井', '福山', '山形', '日比野', '豊田', '橘', '鹿島', '小野', '橘', '小松', '久保', '大貫', '小市', '川島', '飯野', '小川', '神保', '藤木', '杉本', '平田', '上村', '徳永', '比嘉', '羽田', '林', '島田', '川添', '吉田', '安永', '依田', '平松', '瀬戸内', '柳川', '小栗', '秋田', '高嶋', '金森', '菊地', '谷本', '長田', '曽我', '風間', '小柳', '富永', '楠', '安部', '関', '金井', '沖', '溝口', '大倉', '荻原', '清田', '田島', '榎本', '池内', '岸部', '田沢', '岡田', '伊集院', '奥村', '大井', '奥貫', '生瀬', '松岡', '鈴木', '川本', '片平', '黒川', '長澤', '滝川', '谷村', '田辺', '大坂', '笠井', '川辺', '堀口', '大崎', '永井', '豊原', '長友', '高見', '藤井', '大内', '早川', '内田', '黒木', '水谷', '大倉', '武内', '高尾', '西川', '鹿賀', '岡本', '西山', '中山'],

	username_formats: [
		'{{last_name}}{{first_name}}'
	],

	name_formats: [
		'{{full_name}}{{name_prefix}}'
	],

	full_name_formats: [
		'{{last_name}}{{first_name}}'
	],

	company_name_formats: [
		'{{last_name}}{{company_suffix}}'
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
		return this.numerify('#' + this.word + '##');
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
