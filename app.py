from flask import Flask, render_template, request, jsonify
import re
import oct2py

app = Flask(__name__)

oc = oct2py.Oct2Py()
oc.addpath('/Users/suever/Development/MATL')


def parseError(message):
    """
    Parses the error messages returned by oct2py
    """
    match = re.search('(?<=Octave returned:\n).*', message, re.DOTALL)
    if match is not None:
        message = match.group()

    return message


def matl(flags, code='', inputs='', outfile='defout'):
    """
    Opens a session with Octave and manages input/output as well as errors
    """

    result = {}

    try:
        oc.matl_runner(flags, code, inputs, outfile)
    except Exception as e:
        result['error'] = parseError(e.message)

    # Check to see if there is any output
    with open(outfile, 'r') as fid:
        result['output'] = fid.read()

    return jsonify(result), 200


@app.route('/')
def home():
    code = request.values.get('code', '')
    inputs = request.values.get('inputs', '')
    return render_template('index.html', code=code, inputs=inputs)


@app.route('/explain', methods=['POST', 'GET'])
def explain():
    code = request.values.get('code', '')
    return matl('-eo', code)


@app.route('/run', methods=['POST'])
def run():
    inputs = request.values.get('inputs', '')
    code = request.values.get('code', '')

    return matl('-ro', code, inputs)


app.run(debug=True)
