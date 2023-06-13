export const includes = {
  transform(parameters) {
    const [array, value] = Object.values(parameters);

    return Array.isArray(array) ? array.includes(value) : false;
  },
};

export const uppercase = {
  transform(parameters) {
    const string = parameters[0];

    return typeof string === 'string' ? string.toUpperCase() : string;
  },
};
