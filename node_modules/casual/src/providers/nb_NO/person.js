var provider = {

	phone_formats: [
		'## ## ## ##'
	],

	// 50 most popular names of newborne females in 2016
	first_names_female: [
		'Nora', 'Emma', 'Sara', 'Sofie', 'Sofia', 'Maja', 'Olivia', 'Ella', 'Ingrid', 'Emilie',
		'Leah', 'Anna', 'Tiril', 'Thea', 'Hanna', 'Linnea', 'Ida', 'Mia', 'Aurora', 'Mathilde',
		'Frida', 'Lilly', 'Julie', 'Amalie', 'Vilde', 'Jenny', 'Astrid', 'Tuva', 'Alma', 'Amanda',
		'Victoria', 'Hedda', 'Maria', 'Oda', 'Marie', 'Elise', 'Ada', 'Iben', 'Eline', 'Selma',
		'Live', 'Mina', 'Oline', 'Mathea', 'Julia', 'Ellinor', 'Eva', 'Agnes', 'Amelia', 'Mille'
	],

	// 50 most popular names of newbornes males in 2016
	first_names_male: [
		'William', 'Oskar', 'Lucas', 'Mathias', 'Filip', 'Oliver', 'Jakob', 'Emil', 'Noah', 'Aksel',
		'Henrik', 'Elias', 'Kasper', 'Jonas', 'Liam', 'Theodor', 'Markus', 'Alexander', 'Tobias', 'Magnus',
		'Håkon', 'Isak', 'Matheo', 'Benjamin', 'Sebastian', 'Martin', 'Kristian', 'Olav', 'Ludvig', 'Mohammad',
		'Adrian', 'Sander', 'Nikolai', 'Johannes', 'Leon', 'Victor', 'Theo', 'Mikkel', 'Erik', 'Johan',
		'Daniel', 'Jonathan', 'Ulrik', 'Even', 'Iver', 'Andreas', 'Julian', 'Odin', 'Felix', 'Sigurd'
	],

	first_names: function () {
		return this.first_names_female.concat(this.first_names_male);
	},

	// 100 most used surnames in 2013
	last_names: [
		'Hansen', 'Johansen', 'Olsen', 'Larsen', 'Andersen', 'Pedersen', 'Nilsen', 'Kristiansen', 'Jensen', 'Karlsen',
		'Johnsen', 'Pettersen', 'Eriksen', 'Berg', 'Haugen', 'Hagen', 'Johannessen', 'Andreassen', 'Jacobsen', 'Dahl',
		'Jørgensen', 'Halvorsen', 'Henriksen', 'Lund', 'Sørensen', 'Jakobsen', 'Gundersen', 'Moen', 'Iversen', 'Svendsen',
		'Strand', 'Solberg', 'Martinsen', 'Paulsen', 'Knutsen', 'Eide', 'Bakken', 'Kristoffersen', 'Mathisen', 'Lie',
		'Rasmussen', 'Amundsen', 'Lunde', 'Kristensen', 'Bakke', 'Berge', 'Moe', 'Nygård', 'Fredriksen', 'Solheim',
		'Nguyen', 'Lien', 'Holm', 'Andresen', 'Christensen', 'Hauge', 'Knudsen', 'Nielsen', 'Evensen', 'Sæther',
		'Aas', 'Hanssen', 'Myhre', 'Haugland', 'Thomassen', 'Simonsen', 'Sivertsen', 'Berntsen', 'Danielsen', 'Ali',
		'Arnesen', 'Rønning', 'Næss', 'Sandvik', 'Antonsen', 'Haug', 'Ellingsen', 'Edvardsen', 'Vik', 'Thorsen',
		'Gulbrandsen', 'Isaksen', 'Birkeland', 'Ruud', 'Ahmed', 'Strøm', 'Aasen', 'Ødegård', 'Jenssen', 'Tangen',
		'Eliassen', 'Myklebust', 'Bøe', 'Mikkelsen', 'Aune', 'Helland', 'Tveit', 'Abrahamsen', 'Brekke', 'Madsen'
	],

	phone: function () {
		return this.numerify(this.random_element(this.phone_formats));
	}

};

module.exports = provider;
