var provider = {
	phone_formats: [
		'##-######',
		'###-######',
		'07##-######',
		'07## ## ## ##',
		'07## ### ###',
	],

	company_suffixes: ['AB', 'HB', 'Aktiebolag', 'Handelsbolag'],

	first_name_females: [
		'Maria', 'Anna', 'Margareta', 'Elisabeth', 'Eva', 'Kristina',
		'Birgitta', 'Karin', 'Elisabet', 'Marie', 'Ingrid', 'Christina',
		'Linnéa', 'Sofia', 'Kerstin', 'Marianne', 'Lena', 'Helena', 'Emma',
		'Johanna', 'Linnea', 'Inger', 'Sara', 'Cecilia', 'Elin', 'Anita',
		'Ulla', 'Louise', 'Gunilla', 'Viola', 'Linda', 'Ida', 'Susanne',
		'Hanna', 'Malin', 'Katarina', 'Jenny', 'Carina', 'Elsa', 'Irene',
		'Monica', 'Barbro', 'Ulrika', 'Viktoria', 'Astrid', 'Annika', 'Julia',
		'Alice', 'Åsa', 'Matilda', 'Siv', 'Amanda', 'Therese', 'Britt',
		'Yvonne', 'Camilla', 'Ann', 'Ingegerd', 'Agneta', 'Lovisa', 'Caroline',
		'Lisa', 'Gun', 'Charlotte', 'Anette', 'Sandra', 'Frida', 'Sofie',
		'Berit', 'Margaretha', 'Emelie', 'Inga', 'Charlotta', 'Alexandra',
		'Erika', 'Emilia', 'Ebba', 'Anneli', 'Ellen', 'Victoria', 'Jessica',
		'Ingeborg', 'Märta', 'Maja', 'Birgit', 'Gunnel', 'Pia', 'Olivia',
		'Madeleine', 'Sonja', 'Mona', 'Agnes', 'Felicia', 'Karolina', 'Josefin',
		'Monika', 'Helen', 'Magdalena', 'Gerd', 'Lina',
	],

	first_name_males: [
		'Erik', 'Lars', 'Karl', 'Anders', 'Johan', 'Per', 'Nils', 'Carl',
		'Mikael', 'Jan', 'Hans', 'Lennart', 'Olof', 'Peter', 'Gunnar', 'Sven',
		'Fredrik', 'Bengt', 'Bo', 'Daniel', 'Gustav', 'Åke', 'Göran',
		'Alexander', 'Magnus', 'Martin', 'Andreas', 'Stefan', 'John', 'Leif',
		'Mats', 'Ulf', 'Björn', 'Thomas', 'Henrik', 'Bertil', 'Jonas', 'Arne',
		'Christer', 'Axel', 'Ingemar', 'Robert', 'David', 'Kjell', 'Emil',
		'Stig', 'Håkan', 'Rolf', 'Mattias', 'Oskar', 'Roland', 'William',
		'Tommy', 'Patrik', 'Michael', 'Gustaf', 'Joakim', 'Ingvar', 'Simon',
		'Christian', 'Roger', 'Marcus', 'Sebastian', 'Anton', 'Oscar', 'Olov',
		'Eric', 'Tomas', 'Viktor', 'Johannes', 'Tobias', 'Ove', 'Kent',
		'Niklas', 'Emanuel', 'Hugo', 'Rune', 'Jörgen', 'Robin', 'Elias',
		'Gösta', 'Adam', 'Kenneth', 'Filip', 'Kurt', 'Linus', 'Wilhelm', 'Sten',
		'Alf', 'Arvid', 'Dan', 'Jonathan', 'Rickard', 'Ali', 'Albin', 'Börje',
		'Vilhelm', 'Torbjörn', 'Claes', 'Jesper',
	],

	last_names: [
		'Johansson', 'Andersson', 'Karlsson', 'Nilsson', 'Eriksson', 'Larsson',
		'Olsson', 'Persson', 'Svensson', 'Gustafsson', 'Pettersson', 'Jonsson',
		'Jansson', 'Hansson', 'Bengtsson', 'Jönsson', 'Carlsson', 'Petersson',
		'Lindberg', 'Magnusson', 'Lindström', 'Gustavsson', 'Olofsson',
		'Lindgren', 'Axelsson', 'Bergström', 'Lundberg', 'Lundgren',
		'Jakobsson', 'Berg', 'Berglund', 'Sandberg', 'Fredriksson', 'Mattsson',
		'Henriksson', 'Sjöberg', 'Forsberg', 'Lindqvist', 'Lind', 'Engström',
		'Eklund', 'Lundin', 'Danielsson', 'Håkansson', 'Holm', 'Gunnarsson',
		'Bergman', 'Samuelsson', 'Fransson', 'Nyström', 'Lundqvist', 'Johnsson',
		'Holmberg', 'Björk', 'Wallin', 'Ali', 'Arvidsson', 'Söderberg',
		'Nyberg', 'Isaksson', 'Nordström', 'Mårtensson', 'Lundström',
		'Björklund', 'Eliasson', 'Berggren', 'Sandström', 'Nordin', 'Ström',
		'Åberg', 'Hermansson', 'Ekström', 'Holmgren', 'Hedlund', 'Sundberg',
		'Sjögren', 'Dahlberg', 'Ahmed', 'Martinsson', 'Öberg', 'Månsson',
		'Hellström', 'Strömberg', 'Abrahamsson', 'Blom', 'Ek', 'Blomqvist',
		'Åkesson', 'Norberg', 'Falk', 'Sundström', 'Lindholm', 'Jonasson',
		'Åström', 'Löfgren', 'Andreasson', 'Dahl', 'Söderström', 'Jensen',
		'Ivarsson',
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
