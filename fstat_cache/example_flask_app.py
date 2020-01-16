import fstat_cache
from flask import Flask
import os.path
app = Flask(__name__)
cache = fstat_cache.FStatCache()
cache.build(["/tmp/test_file_1"])


@app.route('/cache/<name>')
def using_cache(name):
    file = "/tmp/{}".format(name)
    if not os.path.isfile(file):
        return "no such file {}".format(file)
    return cache.get_file_stats(file)


@app.route('/stat/<name>')
def using_stat(name):
    file = "/tmp/{}".format(name)
    if not os.path.isfile(file):
        return "no such file {}".format(file)
    return cache.get_file_stats_using_stat(file)


if __name__ == '__main__':
    try:
        app.run()
    except KeyboardInterrupt:
        cache.invalidate()
