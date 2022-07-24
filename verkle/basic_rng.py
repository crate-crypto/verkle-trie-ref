import hashlib


class BasicPRNG():
    def __init__(self, seed):
        # Seed should be a 32 byte array
        self.seed = seed
        # Counter is seen as a 64 bit unsigned integer
        self.counter = 0

    #  Returns a pseudo random 32 byte array
    def rand_bytes(self):
        sha = hashlib.sha256()

        counter_bytes = self.counter.to_bytes(8, "little")
        sha.update(counter_bytes)
        sha.update(self.seed)

        result = sha.digest()

        self.counter = self.counter + 1

        return result

    #  Returns `num_values` pseudo random 32 byte arrays
    def rand_vec_bytes(self, num_values):
        list = []
        for _ in range(num_values):
            list.append(self.rand_bytes())
        return list
