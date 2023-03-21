var moment = require('moment');

var provider = {
  moment: function() {
    moment.locale('bg')
    return moment.unix(this.unix_time);
  },
};

module.exports = provider;
