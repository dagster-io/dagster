var helpers = require('./helpers');
var exists = require('fs').existsSync;

var safe_require = function(filename) {
	if (exists(filename + '.js')) {
		return require(filename);
	}
	return {};
};

var build_casual = function() {
	var casual = helpers.extend({}, helpers);

	casual.functions = function() {
		var adapter = {};

		Object.keys(this).forEach(function(name) {
			if (name[0] === '_') {
				adapter[name.slice(1)] = casual[name];
			}
		});

		return adapter;
	};

	var providers = [
		'address',
		'text',
		'internet',
		'person',
		'number',
		'date',
		'payment',
		'misc',
		'color'
	];

	casual.register_locale = function(locale) {
		casual.define(locale, function() {
			var casual = build_casual();

			providers.forEach(function(provider) {
				casual.register_provider(helpers.extend(
					require('./providers/' + provider),
					safe_require(__dirname + '/providers/' + locale + '/' + provider)
				));
			});

			return casual;
		});
	}

	var locales = [
		'en_US',
		'ru_RU',
		'uk_UA',
		'nl_NL',
		'en_CA',
		'fr_FR',
		'id_ID',
		'it_CH',
		'it_IT',
		'de_DE',
		'ar_SY',
		'pt_BR',
		'nb_NO',
		'ro_RO',
		'sv_SE',
		'bg_BG',
		'ja_JP',
		'da_DK'
	];

	locales.forEach(casual.register_locale);

	return casual;
};

// Default locale is en_US
module.exports = build_casual().en_US;
