export type OmitTypename<T> = {
  [K in keyof T as K extends '__typename' ? never : K]: T[K] extends Array<infer U>
    ? Array<U extends {__typename: string} ? OmitTypename<Omit<U, '__typename'>> : OmitTypename<U>>
    : T[K] extends {__typename: string}
    ? OmitTypename<Omit<T[K], '__typename'>>
    : T[K];
};
