import pickle


class FileMarshalable:
    def marshal_value(self, value, to_file):
        with open(to_file, 'wb') as ff:
            pickle.dump(value, ff)

    def unmarshal_value(self, from_file):
        with open(from_file, 'rb') as ff:
            return pickle.load(ff)
