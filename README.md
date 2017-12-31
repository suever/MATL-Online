# MATL Online

[![Build Status](https://travis-ci.org/suever/MATL-Online.svg?branch=master)](https://travis-ci.org/suever/MATL-Online)
[![Coverage Status](https://coveralls.io/repos/github/suever/MATL-Online/badge.svg?branch=master)](https://coveralls.io/github/suever/MATL-Online?branch=master)
[![Code Climate](https://codeclimate.com/github/suever/MATL-Online/badges/gpa.svg)](https://codeclimate.com/github/suever/MATL-Online) 
[![Updates](https://pyup.io/repos/github/suever/MATL-Online/shield.svg)](https://pyup.io/repos/github/suever/MATL-Online/)

This is a Python-based online interpreter for the [MATL][matl] programming language, a golfing language based on [MATLAB][matlab] and [Octave][octave]. A live version of this application is hosted at [matl.suever.net][matl.suever.net].

### The Stack

The core of the application is the lightweight Python web framework, [Flask][flask]. Two-way communication between the JavaScript front-end and the application is handled by [SocketIO][socketio]. MATL code and input arguments are submitted to the server and [celery][celery] assigns the task to one of many available worker processes. Each worker process uses the [`octave_kernel`][octave_kernel] library to communicate with an underlying [Octave][octave] instance to evaluate the provided code. All [Octave][octave] output from the process (including text and graphics) is streamed in real-time back to the browser via [SocketIO][socketio]. 

Technologies: [jQuery][jquery], [SocketIO][socketio], [flask][flask], [flask-socketio][flask-socketio], [celery][celery], [octave_kernel][octave_kernel], [Octave][octave]


### Planned Future Improvements

- Ability to run multiple test cases sequentially
- [Docker container][docker] to easily run the application locally with minimal configuration
- Analytics of all MATL answers on the [Programming Puzzle and Code Golf Stack Exchange site][ppcg] including top users, top questions, and common usage patterns.

### Contributing

We welcome contributions from any member of the user community. Free free to [submit a pull request][pullrequest] or [open an issue][issues] with your contributions.

### License

This software is licensed under the MIT License.

[matl]: https://github.com/lmendo/MATL
[matl.suever.net]: https://matl.suever.net/
[docker]: https://www.docker.com/
[ppcg]: https://codegolf.stackexchange.com
[pullrequest]: https://github.com/suever/MATL-Online/pulls
[issues]: https://github.com/suever/MATL-Online/issues/new
[socketio]: http://socket.io/
[flask]: https://flask.pocoo.org
[octave]: https://www.gnu.org/software/octave/
[matlab]: https://www.mathworks.com/products/matlab/
[celery]: http://www.celeryproject.org/
[octave_kernel]: https://github.com/Calysto/octave_kernel
[jquery]: https://jquery.com
[flask-socketio]: https://flask-socketio.readthedocs.io/en/latest/
