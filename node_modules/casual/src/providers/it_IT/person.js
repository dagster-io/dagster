var provider = {

  phone_formats: ['0# ########', '0### ######', '+393#########'],

  prefix: ['Arch.', 'Avv.', 'Dott.', 'Ing', 'Prof.', 'Sig.', 'Sig.ra' ],

  first_names: ['Alessandra', 'Alessandro', 'Alessia', 'Alessio', 'Andrea', 'Anna', 'Chiara', 'Cristiano', 'Cristina', 'Dario', 'Davide', 'Deborah', 'Diego', 'Elena', 'Elia', 'Elisa', 'Emilia', 'Emma', 'Fabiano', 'Fabio', 'Fiona', 'Gabriele', 'Gabriella', 'Gianluca', 'Gianni', 'Giovanni', 'Giulia', 'Giuliano', 'Giulio', 'Guido', 'Irina', 'Lara', 'Laura', 'Lea', 'Leandro', 'Lena', 'Leonarda', 'Leonardo', 'Lia', 'Lina', 'Lisa', 'Livia', 'Livio', 'Loredana', 'Lorena', 'Luana', 'Luca', 'Luigi', 'Luisa', 'Manuela', 'Manuele', 'Mara', 'Marco', 'Matteo', 'Mattia', 'Mia', 'Nevio', 'Nicola', 'Nicoletta', 'Nina', 'Nino', 'Noemi', 'Nora', 'Olivia', 'Paolo', 'Pier Paolo', 'Pietro', 'Raffaele', 'Raffaella', 'Riccardo', 'Roberta', 'Roberto', 'Samuele', 'Sara', 'Selina', 'Simona', 'Simone', 'Sofia', 'Valentina', 'Valentino'],

  last_names: ['Albertini', 'Albertolli', 'Bassi', 'Beffa', 'Bernasconi', 'Bianchi', 'Conconi', 'de Agostini', 'de Pasquale', 'di Saverio', 'Filippi', 'Filippini', 'Forni', 'Franzini', 'Genasci', 'Genoni', 'Guscetti', 'Leventini', 'Lippolis', 'Lombardi', 'Lusetti', 'Marchetti', 'Motta', 'Orioli', 'Parlato', 'Pedrina', 'Pedrini', 'Penzo', 'Pini', 'Ramelli', 'Ronchi', 'Tapparelli', 'Tonella', 'Trosi', 'Zoppi'],

  phone: function() {
    return this.numerify(this.random_element(this.phone_formats));
  },

};

module.exports = provider;
