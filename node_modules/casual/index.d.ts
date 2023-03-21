declare namespace Casual {
  interface Generators {
    // EMBEDDED GENERATORS
    _country(): string;         // 'United Kingdom'
    _city(): string;            // 'New Ortiz chester'
    _street(): string;               // 'Jadyn Islands'
    _address(): string;              // '6390 Tremblay Pines Suite 784'
    _address1(): string;             // '8417 Veda Circles'
    _address2(): string;              // 'Suite 648'
    _state(): string;                 // 'Michigan'
    _state_abbr(): string;            // 'CO'
    _latitude(): string;              // 90.0610
    _longitude(): string;             // 180.0778
    _building_number(): string;       // 2413

    // Text

    _sentence(): string;                // 'Laborum eius porro consequatur.'
    _title(): string;                   // 'Systematic nobis'
    _text(): string;                    // 'Nemo tempore natus non accusamus eos placeat nesciunt. et fugit ut odio nisi dolore non ... (long text)'
    _description(): string;             // 'Vel et rerum nostrum quia. Dolorum fuga nobis sit natus consequatur.'
    _short_description(): string;       // 'Qui iste similique iusto.'
    _string(): string;                  // 'saepe quia molestias voluptates et'
    _word(): string;                    // 'voluptatem'
    _letter(): string;                  // 'k'

    // Internet
    _ip(): string;            // '21.44.122.149'
    _domain(): string;        // 'darrion.us'
    _url(): string;           // 'germaine.net'
    _email(): string;         // 'Josue.Hessel@claire.us'
    _user_agent(): string;    // 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv():34.0) Gecko/20100101 Firefox/34.0'

    // Person

    _name(): string;             // 'Alberto'
    _username(): string;         // 'Darryl'
    _first_name(): string;       // 'Derek'
    _last_name(): string;        // 'Considine'
    _full_name(): string;        // 'Kadin Torphy'
    _password(): string;         // '(205)580-1350Schumm'
    _name_prefix(): string;      // 'Miss'
    _name_suffix(): string;      // 'Jr.'
    _company_name(): string;     // 'Cole, Wuckert and Strosin'
    _company_suffix(): string;   // 'Inc'
    _catch_phrase(): string;    // 'Synchronised optimal concept'
    _phone(): string;            // '982-790-2592'

    // numbers

    _random(): number;                       // 0.7171590146608651 (core generator)
    _coin_flip(): Boolean;                     // true

    // Date

    _unix_time(): number;                   // 659897901
    _moment(): any;                      // moment.js object see http://momentjs.com/docs/
    _century(): string;                      // 'IV'
    _am_pm(): string;                        // 'am'
    _day_of_year(): number;                  // 323
    _day_of_month(): number;                 // 9
    _day_of_week(): number;                  // 4
    _month_number(): number;                 // 9
    _month_name(): string;                   // 'March'
    _year(): number;                     // 1990
    _timezone(): string;                     // 'America/Miquelon'

    // Payments

    _card_type(): string;             // 'American Express'
    _card_exp(): string;              // '03/04'
    _card_data(): { type: string, number: string, exp: string, holder_name: string };             // { type: 'MasterCard', number: '5307558778577046', exp: '04/88', holder_name: 'Jaron Gibson' }

    // Misc

    _country_code(): string;     // 'ES'
    _language_code(): string;    // 'ru'
    _locale(): string;           // 'hi_IN'
    _mime_type(): string;        // 'audio/mpeg'
    _file_extension(): string;   // 'rtf'
    _uuid(): string;             // '2f4dc6ba-bd25-4e66-b369-43a13e0cf150'

    // Colors

    _color_name(): string;        // 'DarkOliveGreen'
    _safe_color_name(): string;   // 'maroon'
    _rgb_hex(): string;           // '#2e4e1f'
    _rgb_array(): Array<number>        // [ 194, 193, 166 ]
  }

  interface functions {
    // EMBEDDED GENERATORS
    country(): string;         // 'United Kingdom'
    city(): string;            // 'New Ortiz chester'
    street(): string;               // 'Jadyn Islands'
    address(): string;              // '6390 Tremblay Pines Suite 784'
    address1(): string;             // '8417 Veda Circles'
    address2(): string;              // 'Suite 648'
    state(): string;                 // 'Michigan'
    state_abbr(): string;            // 'CO'
    latitude(): string;              // 90.0610
    longitude(): string;             // 180.0778
    building_number(): string;       // 2413

    // Text

    sentence(): string;                // 'Laborum eius porro consequatur.'
    title(): string;                   // 'Systematic nobis'
    text(): string;                    // 'Nemo tempore natus non accusamus eos placeat esciunt. et fugit ut odio nisi dolore non ... (long text)'
    description(): string;             // 'Vel et rerum nostrum quia. Dolorum fuga nobis sit atus consequatur.'
    short_description(): string;       // 'Qui iste similique iusto.'
    string(): string;                  // 'saepe quia molestias voluptates et'
    word(): string;                    // 'voluptatem'
    letter(): string;                  // 'k'

    // Internet
    ip(): string;            // '21.44.122.149'
    domain(): string;        // 'darrion.us'
    url(): string;           // 'germaine.net'
    email(): string;         // 'Josue.Hessel@claire.us'
    user_agent(): string;    // 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv():34.0) Gecko/20100101 Firefox/34.0'

    // Person

    name(): string;             // 'Alberto'
    username(): string;         // 'Darryl'
    first_name(): string;       // 'Derek'
    last_name(): string;        // 'Considine'
    full_name(): string;        // 'Kadin Torphy'
    password(): string;         // '(205)580-1350Schumm'
    name_prefix(): string;      // 'Miss'
    name_suffix(): string;      // 'Jr.'
    company_name(): string;     // 'Cole, Wuckert and Strosin'
    company_suffix(): string;   // 'Inc'
    catch_phrase(): string;    // 'Synchronised optimal concept'
    phone(): string;            // '982-790-2592'

    // numbers

    random(): number;                       // 0.7171590146608651 (core generator)
    coin_flip(): Boolean;                     // true

    // Date

    unix_time(): number;                   // 659897901
    moment(): any;                      // moment.js object see http://momentjs.com/docs/
    century(): string;                      // 'IV'
    am_pm(): string;                        // 'am'
    day_of_year(): number;                  // 323
    day_of_month(): number;                 // 9
    day_of_week(): number;                  // 4
    month_number(): number;                 // 9
    month_name(): string;                   // 'March'
    year(): number;                     // 1990
    timezone(): string;                     // 'America/Miquelon'

    // Payments

    card_type(): string;             // 'American Express'
    card_exp(): string;              // '03/04'
    card_data(): { type: string, number: string, exp: string, holder_name: string };             // { type: 'MasterCard', number: '5307558778577046', exp: '04/88', holder_name: 'Jaron Gibson' }

    // Misc

    country_code(): string;     // 'ES'
    language_code(): string;    // 'ru'
    locale(): string;           // 'hi_IN'
    mime_type(): string;        // 'audio/mpeg'
    file_extension(): string;   // 'rtf'
    uuid(): string              // '2f4dc6ba-bd25-4e66-b369-43a13e0cf150'

    // Colors

    color_name(): string;        // 'DarkOliveGreen'
    safe_color_name(): string;   // 'maroon'
    rgb_hex(): string;           // '#2e4e1f'
    rgb_array(): Array<number>        // [ 194, 193, 166 ]
  }

  interface Casual {
    // EMBEDDED GENERATORS
    country: string;         // 'United Kingdom'
    city: string;            // 'New Ortiz chester'
    zip(digits: Object): string; // '26995-7979' (if no digits specified then random selection between ZIP and ZIP+4)
    street: string;               // 'Jadyn Islands'
    address: string;              // '6390 Tremblay Pines Suite 784'
    address1: string;             // '8417 Veda Circles'
    address2: string;              // 'Suite 648'
    state: string;                 // 'Michigan'
    state_abbr: string;            // 'CO'
    latitude: string;              // 90.0610
    longitude: string;             // 180.0778
    building_number: string;       // 2413

    // Text

    sentence: string;                // 'Laborum eius porro consequatur.'
    sentences(n?: number): string;        // 'Dolorum fuga nobis sit natus consequatur. Laboriosam sapiente. Natus quos ut.'
    title: string;                   // 'Systematic nobis'
    text: string;                    // 'Nemo tempore natus non accusamus eos placeat nesciunt. et fugit ut odio nisi dolore non ... (long text)'
    description: string;             // 'Vel et rerum nostrum quia. Dolorum fuga nobis sit natus consequatur.'
    short_description: string;       // 'Qui iste similique iusto.'
    string: string;                  // 'saepe quia molestias voluptates et'
    word: string;                    // 'voluptatem'
    words(n?: number): string;           // 'sed quis ut beatae id adipisci aut'
    array_of_words(n?: number): Array<string>;  // [ 'voluptas', 'atque', 'vitae', 'vel', 'dolor', 'saepe', 'ut' ]
    letter: string;                  // 'k'

    // Internet

    ip: string;            // '21.44.122.149'
    domain: string;        // 'darrion.us'
    url: string;           // 'germaine.net'
    email: string;         // 'Josue.Hessel@claire.us'
    user_agent: string;    // 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0'

    // Person

    name: string;             // 'Alberto'
    username: string;         // 'Darryl'
    first_name: string;       // 'Derek'
    last_name: string;        // 'Considine'
    full_name: string;        // 'Kadin Torphy'
    password: string;         // '(205)580-1350Schumm'
    name_prefix: string;      // 'Miss'
    name_suffix: string;      // 'Jr.'
    company_name: string;     // 'Cole, Wuckert and Strosin'
    company_suffix: string;   // 'Inc'
    catch_phrase: string;    // 'Synchronised optimal concept'
    phone: string;            // '982-790-2592'

    // numbers
    boolean: boolean;
    random: number;                         // 0.7171590146608651 (core generator)
    integer(from?: number, to?: number): number  // 632
    double(from?: number, to?: number): number  // -234.12987444
    array_of_digits(n?: number): Array<number>;            // [ 4, 8, 3, 1, 7, 6, 6 ]
    array_of_integers(n?: number): Array<number>;         // [ -105, -7, -532, -596, -430, -957, -234 ]
    array_of_doubles(n?: number): Array<number>;           // [ -866.3755785673857, -166.62194719538093, ...]
    coin_flip: Boolean;                     // true

    // Date

    unix_time: number;                   // 659897901
    moment: any;                      // moment.js object see http://momentjs.com/docs/
    date(format?: string): string;  // '2001-07-06' (see available formatters http://momentjs.com/docs/#/parsing/string-format/)
    time(format?: string): string;    // '03:08:02' (see available formatters http://momentjs.com/docs/#/parsing/string-format/)
    century: string;                      // 'IV'
    am_pm: string;                        // 'am'
    day_of_year: number;                  // 323
    day_of_month: number;                 // 9
    day_of_week: number;                  // 4
    month_number: number;                 // 9
    month_name: string;                   // 'March'
    year: number;                     // 1990
    timezone: string;                     // 'America/Miquelon'

    // Payments

    card_type: string;             // 'American Express'
    card_number(vendor?: string): string;   // '4716506247152101' (if no vendor specified then random)
    card_exp: string;              // '03/04'
    card_data: { type: string, number: string, exp: string, holder_name: string };             // { type: 'MasterCard', number: '5307558778577046', exp: '04/88', holder_name: 'Jaron Gibson' }

    // Misc

    country_code: string;     // 'ES'
    language_code: string;    // 'ru'
    locale: string;           // 'hi_IN'
    mime_type: string;        // 'audio/mpeg'
    file_extension: string;   // 'rtf'
    uuid: string;             // '2f4dc6ba-bd25-4e66-b369-43a13e0cf150'

    // Colors

    color_name: string;        // 'DarkOliveGreen'
    safe_color_name: string;   // 'maroon'
    rgb_hex: string;           // '#2e4e1f'
    rgb_array: Array<number>        // [ 194, 193, 166 ]

    // CUSTOM GENERATORS
    define(type: string, cb: (...args: any[]) => any): void;

    // HELPERS
    random_element(elements: Array<any>): any;
    random_value(obj: Object): any;
    random_key(obj: Object): any;
    populate(str: string): string;
    populate_one_of(arr: Array<string>): string;
    numerify(format: string): string;
    register_provider(provider: Object): void;

    // SEEDING
    seed(n: number): any;

    // GENERATORS functions
    functions(): functions;
  }
}
declare module "casual" {
  const casual: Casual.Generators & Casual.Casual;
  export = casual;
}
