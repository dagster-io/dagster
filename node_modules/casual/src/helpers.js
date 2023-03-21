var number = require('./providers/number');

var random_element = function(array) {
	var index = this.integer(0, array.length - 1);
	return array[index];
};

var random_key = function(object) {
	var keys = Object.keys(object);
	return this.random_element(keys);
};

var random_value = function(object) {
	return object[this.random_key(object)];
};

var register_provider = function(provider) {
	for (var i in provider) {
		this.define(i, provider[i]);
	}
};

var extend = function(a, b) {
	for (var i in b) {
		a[i] = b[i];
	}

	return a;
};

var define = function(name, generator) {
	if (typeof generator != 'function') {
		this[name] = generator;
		return;
	}

	if (generator.length) {
		this[name] = generator.bind(this);
	} else {
		Object.defineProperty(this, name, { 
			get: generator,
			configurable: true
		});
	}

	this['_' + name] = generator.bind(this);
};

var numerify = function(format) {
	return format.replace(/#/g, this._digit);
};

var letterify = function(format) {
	return format.replace(/X/g, this._letter);
};

var join = function() {
	var tokens = Array.prototype.slice.apply(arguments);
	return tokens.filter(Boolean).join(' ');
};

var populate = function(format) {
	var casual = this;
	return format.replace(/\{\{(.+?)\}\}/g, function(match, generator) {
		return casual['_' + generator]();
	});
};

var populate_one_of = function(formats) {
	return this.populate(this.random_element(formats));
};

module.exports = {
	random_element: random_element,
	random_value: random_value,
	random_key: random_key,
	register_provider: register_provider,
	extend: extend,
	define: define,
	numerify: numerify,
	letterify:letterify,
	join: join,
	populate: populate,
	populate_one_of: populate_one_of
};
