
class Printer(object):
    def __init__(self, pre=None, post=None):
        self.pre = pre
        self.post = post

    def __call__(self, func):
        def wrappee(*args, **kwargs):
            if self.pre:
                print("Waiting for {} ...".format(self.pre))

            func(*args, **kwargs)

            if self.post:
                print("{} ...".format(self.post))

        return wrappee