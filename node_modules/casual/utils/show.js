var table = require('text-table'),
    realist = require('realist'),
    casual = require('../'),
    read = require('fs').readFileSync;

var providers = [
	'address',
	'color',
	'date',
	'internet',
	'misc',
	'number',
	'payment',
	'person',
	'text'
];

var usage = function(app) {
	console.log(read(__dirname + '/usage.txt').toString());
	app.stop();
};

var render_table = function(provider_name) {
	provider = require('../src/providers/' + provider_name);

	var result = [];
	for (var generator in provider) {
		if (generator === 'seed') {
			continue;
		}

		if (typeof provider[generator] !== 'function') {
			continue;
		}

		result.push([
			generator,
			casual['_' + generator]()
		]);
	};

	console.log('\nProvider:', provider_name, '\n');
	console.log(table(result));
};

var handler = function(opt, provider) {
	casual = casual[opt.locale || 'en_US'];

	if (!provider) {
		providers.forEach(render_table);
	} else if (providers.indexOf(provider) === -1) {
		usage();
		process.exit();
	} else {
		render_table(provider);
	}
};

var options = {
	locale: ['l', 'locale']
};

var events = {
	'option help': usage
};

realist(handler, options, events);
