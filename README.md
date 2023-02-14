# MATL Online

[![tests](https://github.com/suever/MATL-Online/actions/workflows/tests.yml/badge.svg)](https://github.com/suever/MATL-Online/actions/workflows/tests.yml)
[![Coverage Status](https://coveralls.io/repos/github/suever/MATL-Online/badge.svg?branch=main)](https://coveralls.io/github/suever/MATL-Online?branch=main)
[![Code Climate](https://codeclimate.com/github/suever/MATL-Online/badges/gpa.svg)](https://codeclimate.com/github/suever/MATL-Online)

This is a Python-based online interpreter for the [MATL][matl] programming
language, a golfing language based on [MATLAB][matlab] and [Octave][octave]. A
live version of this application is hosted at
[matl.io][matl.io].

### The Stack

The core of the application is the lightweight Python web framework,
[Flask][flask]. Two-way communication between the JavaScript front-end and the
application is handled by [SocketIO][socketio]. MATL code and input arguments
are submitted to the server and [celery][celery] assigns the task to one of many
available worker processes. Each worker process uses the
[`octave_kernel`][octave_kernel] library to communicate with an underlying
[Octave][octave] instance to evaluate the provided code. All [Octave][octave]
output from the process (including text and graphics) is streamed in real-time
back to the browser via [SocketIO][socketio]. 

Technologies: 
* [jQuery][jquery]
* [SocketIO][socketio]
* [flask][flask]
* [flask-socketio][flask-socketio]
* [celery][celery]
* [octave_kernel][octave_kernel]
* [Octave][octave]

### Running Locally

The easiest way to run the application locally is to use [Docker
Compose][docker-compose] which will start the web service, celery worker, redis
instance, and postgres database. Prior to running `docker-compose`, be sure to
build the local docker image:

```bash
make docker
docker-compose up
```

You will then be able to access the application at http://localhost:5000.


### Planned Future Improvements

- Ability to run multiple test cases sequentially
- Analytics of all MATL answers on the [Programming Puzzle and
  Code Golf Stack Exchange site][ppcg] including top users, top questions, and
  common usage patterns.

### Contributing

We welcome contributions from any member of the user community. Free free to
[submit a pull request][pullrequest] or [open an issue][issues] with your
contributions.

### License

This software is licensed under the MIT License.

[celery]: http://www.celeryproject.org/
[docker]: https://www.docker.com/
[docker-compose]: https://docs.docker.com/compose/
[flask-socketio]: https://flask-socketio.readthedocs.io/en/latest/
[flask]: https://flask.pocoo.org
[issues]: https://github.com/suever/MATL-Online/issues/new
[jquery]: https://jquery.com
[matl.io]: https://matl.io
[matl]: https://github.com/lmendo/MATL
[matlab]: https://www.mathworks.com/products/matlab/
[octave]: https://www.gnu.org/software/octave/
[octave_kernel]: https://github.com/Calysto/octave_kernel
[ppcg]: https://codegolf.stackexchange.com
[pullrequest]: https://github.com/suever/MATL-Online/pulls
[socketio]: http://socket.io/
