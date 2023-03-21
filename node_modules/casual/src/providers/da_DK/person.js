var provider = {
	phone_formats: [
		'## ## ## ##'
	],

	prefix: ['Hr.', 'Fru.', 'Frk.'],

	company_suffixes: ['A/S', 'ApS'],

	first_name_females: [
		'Maria', 'Anna', 'Margarete', 'Elisabeth', 'Eva', 'Birgitte', 'Karin', 
		'Elisabeth', 'Marie', 'Ingrid', 'Christina',
		'Sofia', 'Kerstin', 'Marianne', 'Lena', 'Helena', 'Emma',
		'Johanna', 'Linnea', 'Inger', 'Sara', 'Cecilia', 'Elin', 'Anita',
		'Ulla', 'Louise', 'Gunilla', 'Viola', 'Linda', 'Ida', 'Susanne', 'Sanne',
		'Hanna', 'Malin', 'Jenny', 'Carina', 'Elsa', 'Irene',
		'Monica', 'Barbro', 'Ulrika', 'Viktoria', 'Astrid', 'Annika', 'Julia',
		'Alice', 'Åsa', 'Mathilde', 'Siv', 'Amanda', 'Therese',
		'Yvonne', 'Camilla', 'Anne', 'Agnete', 'Caroline',
		'Lisa', 'Charlotte', 'Anette', 'Sandra', 'Sofie',
		'Berit', 'Margaretha', 'Inga', 'Charlotta', 'Alexandra',
		'Erika', 'Emilie', 'Ellen', 'Victoria', 
		'Maja', 'Birgit', 'Pia', 'Olivia', 'Simone',
		'Sonja', 'Mona', 'Agnes', 'Josefine', 'Monika', 'Helen', 'Magdalena', 'Linea',
	],

	first_name_males: [
		'Erik', 'Lars', 'Karl', 'Anders', 'Johan', 'Per', 'Niels', 'Carl',
		'Mikael', 'Jan', 'Hans', 'Lennart', 'Olaf', 'Peter', 'Gunnar', 'Svend',
		'Fredrik', 'Bent', 'Bo', 'Daniel', 'Gustav', 'Åge', 'Jørgen',
		'Alexander', 'Magnus', 'Martin', 'Andreas', 'Stefan', 'John', 'Leif',
		'Mads', 'Bjørn', 'Thomas', 'Henrik', 'Jonas', 'Arne',
		'Kristoffer', 'Axel', 'Allan', 'Robert', 'David', 'Keld', 'Emil',
		'Stig', 'Rolf', 'Mattias', 'Oskar', 'William',
		'Tommy', 'Patrick', 'Michael', 'Gustav', 'Joakim', 'Simon',
		'Christian', 'Marcus', 'Sebastian', 'Anton', 'Eric', 'Thomas', 'Viktor', 
		'Johannes', 'Tobias', 'Ove', 'Kent',
		'Niklas', 'Emanuel', 'Hugo', 'Rune', 'Sune', 'Elias',
		'Adam', 'Kenneth', 'Filip', 'Kurt', 'Linus', 'Wilhelm', 'Steen',
		'Dan', 'Jonathan', 'Ali', 'Vilhelm', 'Torbjørn', 'Claes', 'Jesper',
		'Jimmie', 'Nikolaj', 'Nikolai', 'Josef'
	],

	last_names: [
		'Nielsen', 'Jensen', 'Hansen', 'Pedersen', 'Andersen', 'Christensen', 'Kristensen', 
		'Larsen', 'Sørensen', 'Rasmussen', 'Jørgensen', 'Holm', 'Petersen', 'Madsen', 'Møller'
	],

	first_name_female: function() {
		return this.random_element(this.first_name_females);
	},

	first_name_male: function() {
		return this.random_element(this.first_name_males);
	},

	first_name: function() {
		if (this.integer % 2) {
			return this.first_name_male;
		}

		return this.first_name_female;
	},
};

module.exports = provider;
