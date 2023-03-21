var glues = ['.', '-', '_', null];

var provider = {
  phone_formats: [
    '02 ### ####', '+359 2 ### ####',
    '032 ### ###', '+359 32 ### ###',
    '052 ### ###', '+359 52 ### ###',
    '056 ### ###', '+359 56 ### ###',
    '042 ### ###', '+359 42 ### ###',
    '082 ### ###', '+359 82 ### ###',
    '064 ### ###', '+359 64 ### ###',
    '044 ### ###', '+359 44 ### ###',
    '058 ### ###', '+359 58 ### ###',
    '062 ### ###', '+359 62 ### ###',
    '087# ### ###', '+359 87# ### ###',
    '088# ### ###', '+359 88# ### ###',
    '089# ### ###', '+359 89# ### ###',
    '098# ### ###', '+359 98# ### ###',
  ],

  prefix: ['г-н', 'г-жа'],


  company_suffixes: ['ЕТ', 'ООД', 'ЕООД', 'АД'],

  female_first_names: [
    'Мария', 'Иванка', 'Елена', 'Йорданка', 'Пенка', 'Маргарита', 'Виолета', 'Лиляна', 'Цветанка',
    'Радка', 'Надежда', 'Марийка', 'Румяна', 'Тодорка', 'Стефка', 'Стоянка', 'Василка', 'Росица',
    'Станка', 'Емилия', 'Донка', 'Милка', 'Величка', 'Райна', 'Анка', 'Красимира', 'Снежана',
    'Мариана', 'Валентина', 'Янка', 'Христина', 'Катя', 'Николина', 'Даниела', 'Татяна', 'Светла',
    'Галина', 'Златка', 'Лилия', 'Екатерина', 'Цветана', 'Недялка', 'Диана', 'Антоанета', 'Павлина',
    'Анна', 'Веселина', 'Славка', 'Марияна', 'Юлия',
  ],

  male_first_names:[
    'Иван', 'Георги', 'Димитър', 'Петър', 'Христо', 'Тодор', 'Николай', 'Васил', 'Стефан', 'Йордан',
    'Стоян', 'Никола', 'Атанас', 'Кирил', 'Ангел', 'Александър', 'Илия', 'Борис', 'Красимир',
    'Петко', 'Пламен', 'Валентин', 'Румен', 'Емил', 'Любомир', 'Владимир', 'Михаил', 'Марин',
    'Костадин', 'Цветан', 'Веселин', 'Асен', 'Симеон', 'Любен', 'Борислав', 'Митко', 'Павел',
    'Антон', 'Славчо', 'Венцислав', 'Валери', 'Методи', 'Божидар', 'Здравко', 'Кольо', 'Димо',
    'Константин', 'Боян', 'Огнян', 'Живко',
  ],

  female_last_names: [
    'Иванова', 'Георгиева', 'Димитрова', 'Петрова', 'Николова', 'Стоянова', 'Христова', 'Тодорова',
    'Илиева', 'Василева', 'Атанасова', 'Петкова', 'Ангелова', 'Колева', 'Йорданова', 'Маринова',
    'Стефанова', 'Попова', 'Михайлова', 'Кръстева', 'Костова', 'Димова', 'Павлова', 'Костадинова',
    'Митева', 'Симеонова', 'Цветкова', 'Александрова', 'Маркова', 'Спасова', 'Лазарова', 'Добрева',
    'Младенова', 'Андреева', 'Янева', 'Радева', 'Русева', 'Янкова', 'Пенева', 'Вълчева',
    'Григорова', 'Кирова', 'Найденова', 'Станчева', 'Алексиева', 'Стойчева', 'Борисова', 'Славова',
    'Станева', 'Панайотова',
  ],

  male_last_names:[
    'Иванов', 'Георгиев', 'Димитров', 'Петров', 'Николов', 'Христов', 'Стоянов', 'Тодоров', 'Илиев',
    'Василев', 'Атанасов', 'Петков', 'Ангелов', 'Колев', 'Йорданов', 'Маринов', 'Стефанов', 'Попов',
    'Михайлов', 'Кръстев', 'Костов', 'Димов', 'Костадинов', 'Павлов', 'Митев', 'Симеонов',
    'Цветков', 'Александров', 'Марков', 'Спасов', 'Лазаров', 'Добрев', 'Андреев', 'Младенов',
    'Русев', 'Вълчев', 'Радев', 'Янев', 'Найденов', 'Пенев', 'Янков', 'Станчев', 'Стойчев',
    'Славов', 'Григоров', 'Киров', 'Алексиев', 'Станев', 'Стойков', 'Борисов',
  ],

  name_formats: [
    'г-жа {{female_full_name}}',
    'г-н {{male_full_name}}',
  ],

  username_formats: [
    '{{female_last_name}}.{{female_first_name}}',
    '{{female_first_name}}.{{female_last_name}}',
    '{{female_first_name}}_{{female_last_name}}',
    '{{female_last_name}}_{{female_first_name}}',
    '{{male_last_name}}.{{male_first_name}}',
    '{{male_first_name}}.{{male_last_name}}',
    '{{male_first_name}}_{{male_last_name}}',
    '{{male_last_name}}_{{male_first_name}}'
  ],

  female_full_name_formats: [
    '{{female_first_name}} {{female_last_name}}',
  ],

  male_full_name_formats: [
    '{{male_first_name}} {{male_last_name}}',
  ],

  full_name_formats: [
    '{{female_first_name}} {{female_last_name}}',
    '{{male_first_name}} {{male_last_name}}',
  ],

  company_name_formats: [
    '{{last_name}} {{company_suffix}}',
    '{{last_name}} {{company_suffix}}',
    '{{last_name}} {{company_suffix}}',
  ],

  username: function() {
    return this.transliterate(this.populate_one_of(this.username_formats)).toLowerCase();
  },

  female_full_name: function() {
    return this.populate_one_of(this.female_full_name_formats);
  },

  male_full_name: function() {
    return this.populate_one_of(this.male_full_name_formats);
  },

  female_first_name: function() {
    return this.random_element(this.female_first_names);
  },

  male_first_name: function() {
    return this.random_element(this.male_first_names);
  },

  female_last_name: function() {
    return this.random_element(this.female_last_names);
  },

  male_last_name: function() {
    return this.random_element(this.male_last_names);
  },

  first_name: function() {
    if (this.boolean) {
      return this.female_first_name;
    }

    return this.male_first_name;
  },

  last_name: function() {
    if (this.boolean) {
      return this.female_last_name;
    }

    return this.male_last_name;
  },
};

module.exports = provider;
