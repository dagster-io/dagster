var provider = {
  top_level_domains: ['com', 'net', 'org', 'info', 'bg', 'me'],

  free_email_domains: ['gmail.com', 'yahoo.com', 'hotmail.com', 'abv.bg', 'dir.bg', 'mail.bg'],

  url_formats: [
    'http://www.{{domain}}/',
    'https://www.{{domain}}/',
    'http://{{domain}}/',
    'https://{{domain}}/',
  ],

  domain_formats: [
    '{{domain_name}}.{{top_level_domain}}',
  ],

  domain_name:  function() {
    if (this.boolean) {
      return this.transliterate(this.first_name).toLowerCase();
    }

    return this.transliterate(this.last_name).toLowerCase();
  },
};

module.exports = provider;
