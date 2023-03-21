var moment = require('moment');
moment.locale('ro');

var provider = {

	date: function (format) {
		format = format || 'DD.MM.YYYY';
		return this.moment.format(format);
	}
}

module.exports = provider;
