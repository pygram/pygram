pygram
======
An open source grammar analyzer that uses [PLY](http://www.dabeaz.com/ply/) under the hood.
Its purpose is to serve as an educational aid for undergraduate students taking an introductory course on compilers.

Demo
====
There is a demo hosted on a Heroku free instance: [http://pygram.herokuapp.com](http://pygram.herokuapp.com).

Installation
============

Ubuntu
------

    $ virtualenv -p `which python3` pygram
    $ source pygram/bin/activate
    $ pip install -r requirements.txt
    $ apt-get install graphviz


Deployment on Heroku
--------------------
In order to install graphviz you need to use a custom buildpack.
The easiest way to do it is to use the [heroku-buildpack-multi](https://github.com/ddollar/heroku-buildpack-multi) together with the [heroku-buildpack-python](https://github.com/heroku/heroku-buildpack-python) and the [heroku-buildpack-graphviz](https://github.com/gokceneraslan/heroku-buildpack-graphviz) buildpacks.

    heroku login
    heroku config:add BUILDPACK_URL:https://github.com/ddollar/heroku-buildpack-multi.git
    heroku config:add PATH:/usr/local/bin:/usr/bin:/bin:/app/bin

To-do
=====
* Add support for localization.
* Add support for LL(1) and LR(1) parsers.
