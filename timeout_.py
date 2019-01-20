import sys
import getopt


def main(argv):
    inputfile = ''
    outputfile = ''
    try:
        opts, args = getopt.getopt(argv, "hi:t:x:", ["id=", "time=", "text="])
    except getopt.GetoptError:
        print('test.py -i <id> -t <time> -x <text>')
        sys.exit(2)
    id = 0
    _time = 0
    text = ''
    for opt, arg in opts:
        if opt == '-h':
            print('test.py -i <id> -t <time> -x <text>')
            sys.exit()
        elif opt in ("-i", "--id"):
            id = arg
        elif opt in ("-t", "--time"):
            _time = arg
        elif opt in ("-x", "--text"):
            text = arg

    import time
    from config import xo, bot, time_sgn
    g = xo(id)
    _time = int(_time)
    text = text.split('\n', maxsplit = 1)
    if _time < 10:
        time.sleep(_time)
    else:
        for _ in range(_time//5):
            time.sleep(5)
            g.pull()
            if not g:
                return 0
    g.pull()
    if _time > 60 or _time < 10 or not(
        not g or not(
            g.tie_id or bool(g.giveup_user)
        )
    ):
        if _time > 10:
            time.sleep(5)
        if len(text) > 1:
            return g.end(text[0], None, text=text[1])
        return g.end(text[0], None, text=time_sgn)


if __name__ == "__main__":
    main(sys.argv[1:])
