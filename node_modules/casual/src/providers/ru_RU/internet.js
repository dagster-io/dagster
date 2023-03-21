var en_to_ru = {
	'а': 'a',   'А': 'A',
	'б': 'b',   'Б': 'B',
	'в': 'v',   'В': 'V',
	'г': 'g',   'Г': 'G',
	'д': 'd',   'Д': 'D',
	'е': 'e',   'Е': 'E',
	'ё': 'jo',  'Ё': 'JO',
	'ж': 'zh',  'Ж': 'ZH',
	'з': 'z',   'З': 'Z',
	'и': 'i',   'И': 'I',
	'й': 'j',   'Й': 'J',
	'к': 'k',   'К': 'K',
	'л': 'l',   'Л': 'L',
	'м': 'm',   'М': 'M',
	'н': 'n',   'Н': 'N',
	'о': 'o',   'О': 'O',
	'п': 'p',   'П': 'P',
	'р': 'r',   'Р': 'R',
	'с': 's',   'С': 'S',
	'т': 't',   'Т': 'T',
	'у': 'u',   'У': 'U',
	'ф': 'f',   'Ф': 'F',
	'х': 'h',   'Х': 'H',
	'ц': 'c',   'Ц': 'C',
	'ч': 'ch',  'Ч': 'CH',
	'ш': 'sh',  'Ш': 'SH',
	'щ': 'sch', 'Щ': 'SCH',
	'ъ': '',    'Ъ': '',
	'ы': 'y',   'Ы': 'Y',
	'ь': '',    'Ь': '',
	'э': 'e',   'Э': 'E',
	'ю': 'ju',  'Ю': 'JU',
	'я': 'ja',  'Я': 'JA',
	' ': '_',
	'і': 'i',   'І': 'I',
	'ї': 'i',   'Ї': 'I'
};

var asciify = function(str) {
	return str.split('').map(function(c) {
		if (en_to_ru[c]) {
			return en_to_ru[c];
		}

		return c;
	}).join('');
};

var provider = {
	free_email_domains: ['yandex.ru', 'ya.ru', 'narod.ru', 'gmail.com', 'mail.ru', 'list.ru', 'bk.ru', 'inbox.ru', 'rambler.ru', 'hotmail.com'],

	top_level_domains: ['com', 'com', 'net', 'org', 'ru', 'ru', 'ru', 'ru'],

	domain: function() {
		return asciify(this.populate_one_of(this.domain_formats));
	},

	email: function() {
		return asciify(this.populate_one_of(this.email_formats));
	},

	url: function() {
		return asciify(this.populate_one_of(this.url_formats));
	}
};

module.exports = provider;
