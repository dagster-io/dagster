function hashCode(str) {
  return str
    .split('')
    .reduce((prevHash, currVal) => ((prevHash << 5) - prevHash + currVal.charCodeAt(0)) | 0, 0);
}

export const getColorForString = (s: string) => {
  const colors = [
    ['bg-yellow-100 text-yellow-800'],
    ['bg-green-100 text-green-800'],
    ['bg-blue-100 text-blue-800'],
    ['bg-red-100 text-red-800'],
    ['bg-indigo-100 text-indigo-800'],
    ['bg-pink-100 text-pink-800'],
    ['bg-purple-100 text-purple-800'],
    ['bg-gray-100 text-gray-800'],
  ];

  return colors[Math.abs(hashCode(s)) % colors.length];
};
