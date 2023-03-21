var casual = require('../');

describe('API', function() {
	var max_times = 10;
	var test = function(name) {
		it('casual.' + name + ' should be ok', function(done) {
			if (typeof casual[name] === 'function') {
				var pivot = casual[name]();
			} else {
				var pivot = casual[name];
			}

			for (var i = 0; i < max_times; i++) {
				if (typeof casual[name] === 'function') {
					var result = casual[name]();
				} else {
					var result = casual[name];
				}

				if (result != pivot) {
					return done();
				}
			}

			done(new Error('Fail'));
		});
	};

	var address = [
		'zip',
		'city',
		'street',
		'address',
		'address1',
		'address2',
		'state',
		'state_abbr',
		'latitude',
		'longitude',
		'country',
		'building_number'
	];

	var text = [
		'sentence',
		'sentences',
		'title',
		'text',
		'description',
		'short_description',
		'string',
		'word',
		'words',
		'array_of_words',
		'letter',
		'letter_phonetic'
	];

	var internet = [
		'ip',
		'domain',
		'url',
		'email'
	];

	var person = [
		'name',
		'username',
		'first_name',
		'last_name',
		'full_name',
		'password',
		'name_prefix',
		'name_suffix',
		'company_name',
		'catch_phrase',
		'phone'
	];

	var number = [
		'integer',
		'double',
		'digit',
		'array_of_digits',
		'array_of_integers',
		'array_of_doubles'
	];

	var date = [
		'unix_time',
		'moment',
		'date',
		'time',
		'century',
		'am_pm',
		'day_of_year',
		'day_of_month',
		'day_of_week',
		'month_number',
		'month_name',
		'year',
		'timezone'
	];

	var payment = [
		'card_type',
		'card_number',
		'card_exp',
		'card_data'
	];

	var misc = [
		'country_code',
		'language_code',
		'locale',
		'currency',
		'currency_code',
		'currency_symbol',
		'currency_name',
		'mime_type',
		'file_extension',
		'boolean',
		'uuid'
	];

	var color = [
		'color_name',
		'safe_color_name',
		'rgb_hex',
		'rgb_array'
	];

	var providers = [
		address,
		text,
		internet,
		person,
		number,
		date,
		payment,
		misc,
		color
	];

	describe('Embedded generators', function() {
		describe('Address address provider', function() {
			address.forEach(test);
		});

		describe('Text provider', function() {
			text.forEach(test);
		});

		describe('Internet provider', function() {
			internet.forEach(test);
		});

		describe('Person provider', function() {
			person.forEach(test);
		});

		describe('Number generator', function() {
			number.forEach(test);
		});

		describe('Date provider', function() {
			date.forEach(test);
		});

		describe('Payment provider', function() {
			payment.forEach(test);
		});

		describe('Misc provider', function() {
			misc.forEach(test);
		});

		describe('Color provider', function() {
			color.forEach(test);
		});
	});

	describe('Casual helpers', function() {
		describe('define', function() {
			it('Should create new casual property if getter doesn\'t have arguments', function() {
				casual.define('wow', function() {
					return 'wow wow';
				});

				casual.wow.should.be.equal('wow wow');
			});

			it('Should create new casual method if getter does have arguments', function() {
				casual.define('x2', function(x) {
					x = x || 2;
					return x * 2;
				});

				casual.x2(3).should.be.equal(6);
			});
		});

		describe('random_element', function() {
			it('Should pick random element from array', function(done) {
				var array = [1,2,3,4,5,23,6,7,8,95,43];
				var pivot = casual.random_element(array);

				for (var i = 0; i < max_times; ++i) {
					if (pivot != casual.random_element(array)) {
						return done();
					}
				}

				done(new Error('Fail'));
			});
		});

		describe('random_key', function() {
			it('Should return random object key', function(done) {
				var key = casual.random_key({ a: 1, b: 2});
				if (key === 'a' || key === 'b') {
					return done();
				}

				done(new Error('Fail'));
			});
		});

		describe('random_value', function() {
			it('Should return random object value', function(done) {
				var key = casual.random_value({ a: 1, b: 2});
				if (key === 1 || key === 2) {
					return done();
				}

				done(new Error('Fail'));
			});
		});

		describe('extend', function() {
			it('Should extend object', function() {
				var result = casual.extend({}, {a: 42});
				result.should.have.property('a', 42);
			});
		});

		describe('numerify', function() {
			it('Should replace every # in string with digit', function() {
				var format = '####';
				var numbers = casual.numerify(format);
				parseInt(numbers).should.be.within(0, 9999);
			});
		});

		describe('letterify',function(){
			it('should replace every X in a string with a letter',function() {
				var re = /^[a-zA-Z]+$/;

				var result = casual.letterify('XXXX');
				re.test(result).should.be.true;

				result = casual.letterify('1234');
				re.test(result).should.be.false;

				result = casual.letterify('X123X');
				re.test(result).should.be.false;
			});
		})

		describe('register_provider', function() {
			it('Should define generators', function() {
				casual.register_provider({
					really_custom_generator: function() { return 'custom' }
				});
				casual.really_custom_generator.should.be.equal('custom');
			});
		});

		describe('join', function() {
			it('Should join strings with spaces like a boss', function() {
				casual.join('wow', 'such', 'sentence').should.be.equal('wow such sentence');
			})
		});
	});

	describe('Generator seeding', function() {
		var create_data_set = function() {
			return {
				description: casual.description,
				text: casual.text,
				random: casual.random,
				integer: casual.integer,
				card_number: casual.card_number,
				phone: casual.phone,
				unix_time: casual.unix_time,
				day_of_year: casual.day_of_year,
				date: casual.date,
				time: casual.time,
				moment_string: casual.moment.toISOString(),
			};
		};

		it('Should repeat random sequence on same seed', function(done) {
			this.timeout(3000);

			var seed = 123;

			casual.seed(seed);
			var set1 = create_data_set();

			setTimeout(function () {
				casual.seed(seed);
				var set2 = create_data_set();

				for (var i in set1) {
					set1[i].should.be.equal(set2[i], i);
				}

				done();
			}, 2001); // Check for date/time perturbation
		})
	});

	var verify_generator = function(generator) {
		var function_name = '_' + generator;
		casual[function_name].should.be.a.Function;

		var seed = 123;

		casual.seed(seed);
		var val = casual[generator];
		val = typeof val === 'function' ? val() : val;

		casual.seed(seed);
		var function_val = casual[function_name]();
		val.should.be.eql(function_val);
	};

	var check_getters = function(generators) {
		generators.forEach(verify_generator);
	};

	describe('Pure getters', function() {
		it('Should have getter function at _{name}', function() {
			providers.forEach(check_getters);
		});

		it('Should return only funtions interface', function() {
			var functions = casual.functions();
			for (var name in functions) {
				if (name === 'seed' || casual.locales.indexOf(name) !== -1) {
					continue;
				}

				var generator = functions[name];
				var seed = 546;

				casual.seed(seed);
				var first = casual['_' + name]();

				casual.seed(seed);
				var second = generator();

				first.should.be.eql(second);
			}
		});
	});
});
