var provider = {

  phone_formats: ['091 ### ## ##', '+41 91 ### ## ##', '079 ### ## ##', '076 ### ## ##'],

  prefix: ['Signora', 'Signor', 'Dr.'],

  first_names: ['Noah', 'Luca', 'David', 'Leon', 'Leandro', 'Nico', 'Levin', 'Julian', 'Tim', 'Ben', 'Gian', 'Jonas', 'Lukas', 'Dario', 'Jan', 'Elias', 'Liam', 'Lionel', 'Samuel', 'Fabio', 'Nevio', 'Matteo', 'Nils', 'Joel', 'Livio', 'Fabian', 'Finn', 'Laurin', 'Robin', 'Simon', 'Elia', 'Gabriel', 'Alexander', 'Nino', 'Luis', 'Andrin', 'Benjamin', 'Louis', 'Diego', 'Lars', 'Rafael', 'Aaron', 'Janis', 'Loris', 'Colin', 'Nicolas', 'Lian', 'Leo', 'Manuel', 'Noel', 'Mia', 'Alina', 'Laura', 'Julia', 'Anna', 'Emma', 'Leonie', 'Lena', 'Lara', 'Elin', 'Elena', 'Lea', 'Sara', 'Nina', 'Chiara', 'Sophia', 'Livia', 'Lia', 'Lina', 'Giulia', 'Jana', 'Sophie', 'Elina', 'Selina', 'Sofia', 'Luana', 'Nora', 'Alessia', 'Emilia', 'Melina', 'Lisa', 'Amélie', 'Lorena', 'Noemi', 'Fiona', 'Valentina', 'Ronja', 'Luisa', 'Sarah', 'Zoe', 'Mila', 'Olivia', 'Emily', 'Leana', 'Ladina', 'Mara', 'Ella', 'Hanna', 'Amelie', 'Elisa'],

  last_names: ['Albertini', 'Albertolli', 'Bassi', 'Beffa', 'Bernasconi', 'De Agostini', 'Dotta', 'Filippi', 'Filippini', 'Forni', 'Genasci', 'Genoni', 'Jelmini', 'Leventini', 'Lombardi', 'Marchetti', 'Pedrina', 'Pedrini', 'Pervangher', 'Peter', 'Pini', 'Ramelli', 'Ronchi', 'Tonella', 'Zoppi', 'Franzini', 'Guscetti', 'Trosi', 'Motta'],

  phone: function() {
    return this.numerify(this.random_element(this.phone_formats));
  },

};

module.exports = provider;
