
class ProgressCounter:
    def __init__(self, total):
        self.total = total
        self.n = 0

    def update(self, n=1):
        self.n += n

    def __enter__(self):
        return self

    def __exit__(self, *args):
        ...
