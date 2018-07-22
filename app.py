from flask import Flask, request, session, g, url_for, \
    render_template, flash
import pigpio
import numpy as np
import os
import time
from helpers import fade_colors


app = Flask(__name__)
app.debug = True

app.config.from_envvar('LIGHT_CONTROLS_SETTINGS', silent=True)


def startup_pigpio():
    global pi1
    os.system('sudo /home/pi/website/startup_commands.sh')
    time.sleep(1)
    pi1 = pigpio.pi()
    pi1.set_PWM_dutycycle(17, 0)
    pi1.set_PWM_dutycycle(27, 0)
    pi1.set_PWM_dutycycle(22, 0)


# don't cache css
@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/climbing')
def climbing():
    return render_template('climbing.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/wildlife')
def wildlife():
    return render_template('wildlife.html')


@app.route('/handler')
def handler():
    return render_template('handler.html')


@app.route('/table')
def table():
    return render_template('table.html')


@app.route('/controls', methods=['GET', 'POST'])
def light_controls():
    # safely try to get the current values of the GPIO Pins. If multiple people
    # are controlling the table, it pulls the current value every time they
    # load it. I could move this into the html so people get live updates
    # TODO: move into html for live update.

    try:
        r = pi1.get_PWM_dutycycle(17)
        g = pi1.get_PWM_dutycycle(27)
        b = pi1.get_PWM_dutycycle(22)
    except AttributeError:
        r = 0
        g = 0
        b = 0
    except:
        print(Exception)

    if request.method == 'POST':
        try:
            new_colors = np.array([request.form['red'], request.form['green'],
                                  request.form['blue']])
            new_colors = new_colors.astype('int')
            assert (np.all(new_colors < 256) and np.all(new_colors >= 0))
            fade_colors(pi1, np.array([r, g, b]), new_colors, [17, 27, 22])
            r = pi1.get_PWM_dutycycle(17)
            g = pi1.get_PWM_dutycycle(27)
            b = pi1.get_PWM_dutycycle(22)
        except (ValueError, AssertionError):
            flash('You need to type a value between 0 and 255 for all boxes')
    return render_template('light_controls.html', r_value=r, g_value=g,
                            b_value=b)


if __name__ == '__main__':
    startup_pigpio()

    app.run()
