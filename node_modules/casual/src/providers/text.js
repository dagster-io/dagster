var first_letter_up = function(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
};

var provider = {
	words_list: [
		'alias', 'consequatur', 'aut', 'perferendis', 'sit', 'voluptatem',
		'accusantium', 'doloremque', 'aperiam', 'eaque','ipsa', 'quae', 'ab',
		'illo', 'inventore', 'veritatis', 'et', 'quasi', 'architecto',
		'beatae', 'vitae', 'dicta', 'sunt', 'explicabo', 'aspernatur', 'aut',
		'odit', 'aut', 'fugit', 'sed', 'quia', 'consequuntur', 'magni',
		'dolores', 'eos', 'qui', 'ratione', 'voluptatem', 'sequi', 'nesciunt',
		'neque', 'dolorem', 'ipsum', 'quia', 'dolor', 'sit', 'amet',
		'consectetur', 'adipisci', 'velit', 'sed', 'quia', 'non', 'numquam',
		'eius', 'modi', 'tempora', 'incidunt', 'ut', 'labore', 'et', 'dolore',
		'magnam', 'aliquam', 'quaerat', 'voluptatem', 'ut', 'enim', 'ad',
		'minima', 'veniam', 'quis', 'nostrum', 'exercitationem', 'ullam',
		'corporis', 'nemo', 'enim', 'ipsam', 'voluptatem', 'quia', 'voluptas',
		'sit', 'suscipit', 'laboriosam', 'nisi', 'ut', 'aliquid', 'ex', 'ea',
		'commodi', 'consequatur', 'quis', 'autem', 'vel', 'eum', 'iure',
		'reprehenderit', 'qui', 'in', 'ea', 'voluptate', 'velit', 'esse',
		'quam', 'nihil', 'molestiae', 'et', 'iusto', 'odio', 'dignissimos',
		'ducimus', 'qui', 'blanditiis', 'praesentium', 'laudantium', 'totam',
		'rem', 'voluptatum', 'deleniti', 'atque', 'corrupti', 'quos',
		'dolores', 'et', 'quas', 'molestias', 'excepturi', 'sint',
		'occaecati', 'cupiditate', 'non', 'provident', 'sed', 'ut',
		'perspiciatis', 'unde', 'omnis', 'iste', 'natus', 'error',
		'similique', 'sunt', 'in', 'culpa', 'qui', 'officia', 'deserunt',
		'mollitia', 'animi', 'id', 'est', 'laborum', 'et', 'dolorum', 'fuga',
		'et', 'harum', 'quidem', 'rerum', 'facilis', 'est', 'et', 'expedita',
		'distinctio', 'nam', 'libero', 'tempore', 'cum', 'soluta', 'nobis',
		'est', 'eligendi', 'optio', 'cumque', 'nihil', 'impedit', 'quo',
		'porro', 'quisquam', 'est', 'qui', 'minus', 'id', 'quod', 'maxime',
		'placeat', 'facere', 'possimus', 'omnis', 'voluptas', 'assumenda',
		'est', 'omnis', 'dolor', 'repellendus', 'temporibus', 'autem',
		'quibusdam', 'et', 'aut', 'consequatur', 'vel', 'illum', 'qui',
		'dolorem', 'eum', 'fugiat', 'quo', 'voluptas', 'nulla', 'pariatur',
		'at', 'vero', 'eos', 'et', 'accusamus', 'officiis', 'debitis', 'aut',
		'rerum', 'necessitatibus', 'saepe', 'eveniet', 'ut', 'et',
		'voluptates', 'repudiandae', 'sint', 'et', 'molestiae', 'non',
		'recusandae', 'itaque', 'earum', 'rerum', 'hic', 'tenetur', 'a',
		'sapiente', 'delectus', 'ut', 'aut', 'reiciendis', 'voluptatibus',
		'maiores', 'doloribus', 'asperiores', 'repellat'
	],

	letters: 'qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM',

	phonetics: [
		'Alfa', 'Bravo', 'Charlie', 'Delta', 'Echo', 'Foxtrot', 'Golf', 'Hotel',
		'India', 'Juliett', 'Kilo', 'Lima', 'Mike', 'November', 'Oscar', 'Papa',
		'Quebec', 'Romeo', 'Sierra', 'Tango', 'Uniform', 'Victor', 'Whiskey',
		'X-ray', 'Yankee', 'Zulu'
	],

	title: function() {
		return first_letter_up(this.words(this.integer(2, 3)));
	},

	sentence: function() {
		return first_letter_up(this.words(this.integer(3, 10))) + '.';
	},

	text: function() {
		return this.sentences(this.integer(3, 6));
	},

	description: function() {
		return this.sentences(this.integer(2, 5));
	},

	short_description: function() {
		return this.sentence;
	},

	string: function() {
		return this.words();
	},

	sentences: function(n) {
		n = n || 3;

		var result = [];
		for (var i = 0; i < n; ++i) {
			result.push(this.sentence);
		}

		return result.join(' ');
	},

	word: function() {
		return this.random_element(this.words_list);
	},

	words: function(n) {
		return this.array_of_words(n).join(' ');
	},

	array_of_words: function(n) {
		n = n || 7;
		var result = [];

		for (var i = 0; i < n; ++i) {
			result.push(this.word);
		}

		return result;
	},

	letter: function() {
		return this.random_element(this.letters);
	},

	letter_phonetic: function() {
		return this.random_element(this.phonetics);
	}
};

module.exports = provider;
