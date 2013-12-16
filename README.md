pygram
======
An open source grammar analyzer that uses [PLY](http://www.dabeaz.com/ply/) under the hood.
Its purpose is to serve as an educational aid for undergraduate students taking an introductory course on compilers.

Features
========
* SLR(1) and LALR(1) grammar support.
* Augmented grammar.
* First and follow sets.
* Automaton state graph visualization.
* Parsing table.
* Parser simulator.

Demo
====
There is a demo hosted on a Heroku free instance: [http://pygram.herokuapp.com](http://pygram.herokuapp.com).

![alt text](http://i.imgur.com/xmMg8oE.png "Preview")

Example
------------

**Terminals**

    OPMULT OPDIV
    OPADD OPSUB
    FACTOR

**Productions**

    expr: expr OPADD term
           | expr OPSUB term
           | term;
    term: term OPMULT FACTOR
           | term OPDIV FACTOR
           | FACTOR; 

Installation
============

Dependencies
------------
The following are the main dependencies used by pygram, for the complete list refer to 'requirements.txt'.

* flask: [http://flask.pocoo.org/](http://flask.pocoo.org/).
* graphviz: [http://www.graphviz.org/](http://www.graphviz.org/).
* ply: [http://www.dabeaz.com/ply/](http://www.dabeaz.com/ply/).
* pydot: [https://bitbucket.org/prologic/pydot/overview](https://bitbucket.org/prologic/pydot/overview).

Note: pydot is included in the src folder 'pydot/'

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

Similar tools
=============
The following is a list of other grammar analyzers. Please, feel free to add more references to the list below.
* [Anagra](http://webdiis.unizar.es/~ezpeleta/doku.php?id=material_de_apoyo)

License
=======
Pygram uses the [MIT](http://opensource.org/licenses/MIT) license.
The dependencies used by Pygram are subject to their respective licenses.
