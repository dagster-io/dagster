@0x82a469a9a185d176;

struct Map(Key, Value) {
  entries @0 :List(Entry);
  struct Entry {
    key @0 :Key;
    value @1 :Value;
  }
}

struct Set(Item) {
  items @0 :List(Item);
}

struct Test {
  intlist @0 :Set(Int64);
}