## Fake data generator [![Build Status](https://travis-ci.org/boo1ean/casual.svg?branch=master)](https://travis-ci.org/boo1ean/casual)

## Installation

> npm install casual

## Usage

```javascript
var casual = require('casual');

// Generate random sentence
// You don't need function call operator here
// because most of generators use properties mechanism
var sentence = casual.sentence;

// Generate random city name
var city = casual.city;

// Define custom generator
casual.define('point', function() {
	return {
		x: Math.random(),
		y: Math.random()
	};
});

// Generate random point
var point = casual.point;

// And so on..
```

Casual uses javascript properties for common generators so you don't need to use function call operator

## Embedded generators

```javascript

// Address

casual.country              // 'United Kingdom'
casual.city                 // 'New Ortiz chester'
casual.zip(digits = {5, 9}) // '26995-7979' (if no digits specified then random selection between ZIP and ZIP+4)
casual.street               // 'Jadyn Islands'
casual.address              // '6390 Tremblay Pines Suite 784'
casual.address1             // '8417 Veda Circles'
casual.address2             // 'Suite 648'
casual.state                // 'Michigan'
casual.state_abbr           // 'CO'
casual.latitude             // 90.0610
casual.longitude            // 180.0778
casual.building_number      // 2413

// Text

casual.sentence               // 'Laborum eius porro consequatur.'
casual.sentences(n = 3)       // 'Dolorum fuga nobis sit natus consequatur. Laboriosam sapiente. Natus quos ut.'
casual.title                  // 'Systematic nobis'
casual.text                   // 'Nemo tempore natus non accusamus eos placeat nesciunt. et fugit ut odio nisi dolore non ... (long text)'
casual.description            // 'Vel et rerum nostrum quia. Dolorum fuga nobis sit natus consequatur.'
casual.short_description      // 'Qui iste similique iusto.'
casual.string                 // 'saepe quia molestias voluptates et'
casual.word                   // 'voluptatem'
casual.words(n = 7)           // 'sed quis ut beatae id adipisci aut'
casual.array_of_words(n = 7)  // [ 'voluptas', 'atque', 'vitae', 'vel', 'dolor', 'saepe', 'ut' ]
casual.letter                 // 'k'

// Internet

casual.ip           // '21.44.122.149'
casual.domain       // 'darrion.us'
casual.url          // 'germaine.net'
casual.email        // 'Josue.Hessel@claire.us'
casual.user_agent   // 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0'

// Person

casual.name            // 'Alberto'
casual.username        // 'Darryl'
casual.first_name      // 'Derek'
casual.last_name       // 'Considine'
casual.full_name       // 'Kadin Torphy'
casual.password        // '(205)580-1350Schumm'
casual.name_prefix     // 'Miss'
casual.name_suffix     // 'Jr.'
casual.company_name    // 'Cole, Wuckert and Strosin'
casual.company_suffix  // 'Inc'
casual.catch_phrase    // 'Synchronised optimal concept'
casual.phone           // '982-790-2592'

// Numbers

casual.random                            // 0.7171590146608651 (core generator)
casual.integer(from = -1000, to = 1000)  // 632
casual.double(from = -1000, to = 1000)   // -234.12987444
casual.array_of_digits(n = 7)            // [ 4, 8, 3, 1, 7, 6, 6 ]
casual.array_of_integers(n = 7)          // [ -105, -7, -532, -596, -430, -957, -234 ]
casual.array_of_doubles(n = 7)           // [ -866.3755785673857, -166.62194719538093, ...]
casual.coin_flip                         // true

// Date

casual.unix_time                    // 659897901
casual.moment                       // moment.js object see http://momentjs.com/docs/
casual.date(format = 'YYYY-MM-DD')  // '2001-07-06' (see available formatters http://momentjs.com/docs/#/parsing/string-format/)
casual.time(format = 'HH:mm:ss')    // '03:08:02' (see available formatters http://momentjs.com/docs/#/parsing/string-format/)
casual.century                      // 'IV'
casual.am_pm                        // 'am'
casual.day_of_year                  // 323
casual.day_of_month                 // 9
casual.day_of_week                  // 4
casual.month_number                 // 9
casual.month_name                   // 'March'
casual.year                         // 1990
casual.timezone                     // 'America/Miquelon'

// Payments

casual.card_type            // 'American Express'
casual.card_number(vendor)  // '4716506247152101' (if no vendor specified then random)
casual.card_exp             // '03/04'
casual.card_data            // { type: 'MasterCard', number: '5307558778577046', exp: '04/88', holder_name: 'Jaron Gibson' }

// Misc

casual.country_code    // 'ES'
casual.language_code   // 'ru'
casual.locale          // 'hi_IN'
casual.currency        // { symbol: 'R', name: 'South African Rand', symbol_native: 'R', decimal_digits: 2, rounding: 0, code: 'ZAR', name_plural: 'South African rand' }		
casual.currency_code   // 'TRY'
casual.currency_symbol // 'TL'
casual.currency_name   // Turkish Lira
casual.mime_type       // 'audio/mpeg'
casual.file_extension  // 'rtf'
casual.boolean         // true
casual.uuid            // '2f4dc6ba-bd25-4e66-b369-43a13e0cf150'

// Colors

casual.color_name       // 'DarkOliveGreen'
casual.safe_color_name  // 'maroon'
casual.rgb_hex          // '#2e4e1f'
casual.rgb_array        // [ 194, 193, 166 ]
```

## Define custom generators

```javascript
casual.define('user', function() {
	return {
		email: casual.email,
		firstname: casual.first_name,
		lastname: casual.last_name,
		password: casual.password
	};
});

// Generate object with randomly generated fields
var user = casual.user;
```

If you want to pass some params to your generator:

```javascript
casual.define('profile', function(type) {
	return {
		title: casual.title,
		description: casual.description,
		type: type || 'private'
	};
});

// Generate object with random data
var profile = casual.profile('public');
```

NOTE: if getter function has non-empty arguments list then generator should be called as function `casual.profile('public')`,
otherwise it should be accessed as property `casual.profile`.

## Localization

You can get localized version of casual generator:

```javascript
var casual = require('casual').ru_RU;
casual.street; // 'Бухарестская'
```

Default locale is `en_US`.

See [src/providers/{{locale}}](https://github.com/boo1ean/casual/blob/master/locales.md) for more details about available locales and locale specific generators.

If you don't find necessary locale, please create an issue or just [add it](#contributing) :)

## Helpers

#### random_element

Get random array element

```javascript
var item = casual.random_element(['ball', 'clock', 'table']);
```

#### random_value

Extract random object value

```javascript
var val = casual.random_value({ a: 1, b: 3, c: 42 });
// val will be equal 1 or 3 or 42
```

#### random_key

Extract random object key

```javascript
var val = casual.random_key({ a: 1, b: 3, c: 42 });
// val will be equal 'a' or 'b' or 'c'
```

#### populate

Replace placeholders with generators results

```javascript
casual.populate('{{email}} {{first_name}}');
// 'Dallin.Konopelski@yahoo.com Lyla'
```

#### populate_one_of

Pick random element from given array and populate it

```javascript
var formats = ['{{first_name}}', '{{last_name}} {{city}}'];
casual.populate_one_of(formats);

// Same as

casual.populate(casual.random_element(formats));
```

#### numerify

Replace all `#` in string with digits

```javascript
var format = '(##)-00-###-##';
casual.numerify(format); // '(10)-00-843-32'
```

#### define

[See custom generators](#define-custom-generators)

#### register_provider

Register generators provider

```javascript
var words = ['flexible', 'great', 'ok', 'good'];
var doge_provider = {
	such: function() {
		return 'such ' + casual.random_element(words);
	},

	doge_phrase: function() {
		return 'wow ' + casual.such();
	}
};

casual.register_provider(doge_provider);

casual.such;        // 'such good'
casual.doge_phrase; // 'wow such flexible'
```

## Seeding

If you want to use a specific seed in order to get a repeatable random sequence:

```javascript
casual.seed(123);
```

It uses [Mersenne Twister](https://github.com/boo1ean/mersenne-twister) pseudorandom number generator in core.

## Generators functions

If you want to pass generator as a callback somewhere or just hate properties you always can access generator **function** at `casual._{generator}`

```javascript
// Generate value using function
var title = casual._title();
// Same as
var title = casual.title;

// Pass generator as callback
var array_of = function(times, generator) {
	var result = [];

	for (var i = 0; i < times; ++i) {
		result.push(generator());
	}

	return result;
};

// Will generate array of five random timestamps
var array_of_timestamps = array_of(5, casual._unix_time);
```

Or you can get functional version of casual generator:

```javascript
var casual = require('casual').functions();

// Generate title
casual.title();

// Generate timestamp
casual.unix_time();
```

## View providers output cli

There is a simple cli util which could be used to view/debug providers output:

	# Will render table with columns [generator_name, result] for all providers
	node utils/show.js

	 # Will render table with columns [generator_name, result] only for person provider
	node utils/show.js person

## Browserify support

Currently you can't use casual with browserify. Please check out this browserify-friendly fork [Klowner/casual-browserify](https://github.com/Klowner/casual-browserify)

## Contributing

- [Adding new locale](https://github.com/boo1ean/casual/blob/master/locales.md)

# License

Heavily inspired by https://github.com/fzaninotto/Faker

The MIT License (MIT)
Copyright (c) 2014 Egor Gumenyuk <boo1ean0807@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.
