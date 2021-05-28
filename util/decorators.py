
class Printer(object):
    """
    This class help you print easily

    Parameters
        pre: prefix print message
        post: post print message
    """
    def __init__(self, pre=None, post=None):
        self.pre = pre
        self.post = post

    def __call__(self, func):
        def wrappee(*args, **kwargs):
            if self.pre:
                print("Waiting for {} ...".format(self.pre))

            f = func(*args, **kwargs)

            if self.post:
                print("{} ...".format(self.post))

            return f

        return wrappee