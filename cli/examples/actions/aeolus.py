

def build(func):
    def inner():
        print("I got decorated")
        func()

    return inner