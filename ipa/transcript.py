import hashlib
from ecc import Banderwagon, Fr


class Transcript():
    def __init__(self,  label):
        self.state = hashlib.sha256()
        self.state.update(label)

    # Convert bytes to scalar field
    def __bytes_to_field(self, bytes):
        return Fr.from_bytes_reduce(bytes)

    def __append_bytes(self, message, label):
        if not isinstance(message, bytes):
            raise TypeError(
                'Expected bytes, but found: {}'.format(type(message)))

        self.state.update(label)
        self.state.update(message)

    def append_scalar(self, scalar, label):
        if not isinstance(scalar, Fr):
            raise TypeError(
                'Expected an Fr type, but found: {}'.format(type(scalar)))

        # Serialize the scalar in little endian
        bytes = scalar.to_bytes()
        self.__append_bytes(bytes, label)

    def append_point(self, point, label):
        if not isinstance(point, Banderwagon):
            raise TypeError(
                'Expected an point type, but found: {}'.format(type(point)))

        point_as_bytes = bytes(point.to_bytes())
        self.__append_bytes(point_as_bytes, label)

    # Produce a challenge based on what has been seen so far in the transcript
    def challenge_scalar(self, label):
        self.domain_sep(label)

        # hash the transcript to produce the challenge
        hash = self.state.digest()
        challenge = self.__bytes_to_field(hash)

        # Clear the sha256 state
        # This step is not completely necessary
        # This is done so it frees memory
        self.state = hashlib.sha256()

        # Add the produced challenge into the new state
        # This is done for two reasons:
        # - It is now impossible for protocols using this
        # class to forget to add any challenges previously seen
        # - It is now secure to repeatedly call for challenges
        self.append_scalar(challenge, label)

        # Return the new challenge
        return challenge

    # domain_sep is used to:
    # - Separate between adding elements to the transcript and squeezing elements out
    # - Separate sub-protocols
    def domain_sep(self, label):
        self.state.update(label)
