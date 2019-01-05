
def err_func():
    c = 5 / 0

if __name__ == '__main__':
    try:
        err_func()

    except Exception as e:
        raise