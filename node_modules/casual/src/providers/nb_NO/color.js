var provider = {

	color_names: [
		'Beige','Svart','Blå','Fiolett','Brun','Rød','Grå','Grønn','Oransje','Turkis','Rosa','Hvit','Gul','Indigo','Lilla'
	],

	color_name: function() {
		return this.random_element(this.color_names);
	}

};

module.exports = provider;
