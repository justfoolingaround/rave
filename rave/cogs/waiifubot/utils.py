import time
from collections import defaultdict


class Ratelimit:
    def __init__(self, exemptions=list(), invert_exemptions=False, *, per=2):
        """
        A basic but powerful ratelimit client to kill spammers.
        """
        self.storage = defaultdict(int)

        self.exemptions = exemptions
        self.invert = invert_exemptions

        self.per = per

    async def perform(self, unique_identifier, task=None):

        if unique_identifier in self.exemptions:
            if not self.invert:
                return False, ((await task()) if task else None)
        else:
            if self.invert:
                return False, ((await task()) if task else None)

        rate_expiration = self.storage[unique_identifier]

        if rate_expiration < time.time():
            self.storage[unique_identifier] = time.time() + self.per
            return False, ((await task()) if task else None)

        return True, None
