const SHORT_ID_LENGTH = 8;

export const shortenId = (id: string) => id.slice(0, SHORT_ID_LENGTH);
