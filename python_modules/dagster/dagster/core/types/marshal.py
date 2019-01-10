import pickle

from abc import ABCMeta, abstractmethod


class MarshallingStrategy(metaclass=ABCMeta):
    @abstractmethod
    def marshal_value(self, value, to_file):
        pass

    @abstractmethod
    def unmarshal_value(self, from_file):
        pass


class PickleMarshallingStrategy(MarshallingStrategy):
    def marshal_value(self, value, to_file):
        with open(to_file, 'wb') as ff:
            pickle.dump(value, ff)

    def unmarshal_value(self, from_file):
        with open(from_file, 'rb') as ff:
            return pickle.load(ff)
