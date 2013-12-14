import re

from flask import Flask
from flask import request
from flask import render_template
from flask import flash

from config import config
from analyzer import create_automaton
from parser import GrammarParser, GrammarSyntaxError, ServerTimeOut

from forms import AnalyzeGrammarForm

app = Flask(__name__)
app.config.update(config)

@app.route('/', methods=['POST', 'GET'])
def analyze_grammar():
    form = AnalyzeGrammarForm(request.form)
    if request.method == 'POST':
        if form.validate():
            terminals = re.split(r'\s+', form.data['terminals'].strip())
            parser = GrammarParser()
            try:
                productions = parser.parse(form.data['productions'])
                start = form.data['start']
                if len(start) == 0:
                    start = None
                automaton,warnings,errors = create_automaton(terminals,productions,start,form.data['type'])
                if automaton:
                    automaton.first = dict((k, v) for k, v in automaton.first.items() if k in automaton.nonterminals)
                    automaton.follow = dict((k, v) for k, v in automaton.follow.items() if k in automaton.nonterminals)
                    return render_template('analyze_grammar.html', form=form, automaton=automaton, warnings=warnings)
                else:
                    form.productions.errors += errors
            except GrammarSyntaxError as e:
                form.productions.errors.append(e.value)
            except ServerTimeOut as e:
                flash(e.value)
 
    return render_template('analyze_grammar.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)
