# -----------------------------------------------------------------------------
# MODPLY is a wrapper around a subset of ply.yacc functionality. 
# Specifically, it subclasses yacc.LRGeneratedTable to overload
# the method lr_parse_table so we're able to extract the lr automaton
# state kernels.
# It uses PLY version 3.4 (as available in december, 2013).
# The following is the copyright notice that accompanies the
# original source code from which this work is derived.
#
#
# ply: yacc.py
#
# Copyright (C) 2001-2011,
# David M. Beazley (Dabeaz LLC)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.  
# * Redistributions in binary form must reproduce the above copyright notice, 
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.  
# * Neither the name of the David Beazley or Dabeaz LLC may be used to
#   endorse or promote products derived from this software without
#  specific prior written permission. 
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# -----------------------------------------------------------------------------
#

import ply
from ply.yacc import Grammar, GrammarError, LALRError


class LRGeneratedTable(ply.yacc.LRGeneratedTable):
    '''
     Class that overloads the lr_parse_table method so
     we can extract the automaton.
    '''

    def __init__(self,grammar,method='LALR',log=None):
        # Add new attribute to record the automaton kernels,
        self.automaton_kernel = {}
        # and call the base constructor.
        super().__init__(grammar,method,log)

    def lr_parse_table(self):
        '''
         A verbatim copy of the overloaded function, save for 
         some additional lines to populate the automaton_kernel
         dictionary.
        '''
        Productions = self.grammar.Productions
        Precedence  = self.grammar.Precedence
        goto   = self.lr_goto         # Goto array
        action = self.lr_action       # Action array
        log    = self.log             # Logger for output

        actionp = { }                 # Action production array (temporary)
        
        log.info("Parsing method: %s", self.lr_method)

        # Step 1: Construct C = { I0, I1, ... IN}, collection of LR(0) items
        # This determines the number of states

        C = self.lr0_items()

        if self.lr_method == 'LALR':
            self.add_lalr_lookaheads(C)

        # Build the parser table, state by state
        st = 0
        for I in C:
            # Loop over each production in I
            actlist = [ ]              # List of actions
            st_action  = { }
            st_actionp = { }
            st_goto    = { }
            log.info("")
            log.info("state %d", st)
            log.info("")
            st_kernel = {}
            for p in I:
                st_kernel[p.number] = [str(p),[]]
                log.info("    (%d) %s", p.number, str(p))
            self.automaton_kernel[st] = st_kernel
            log.info("")

            for p in I:
                    if p.len == p.lr_index + 1:
                        if p.name == "S'":
                            # Start symbol. Accept!
                            st_action["$end"] = 0
                            st_actionp["$end"] = p
                        else:
                            # We are at the end of a production.  Reduce!
                            if self.lr_method == 'LALR':
                                laheads = p.lookaheads[st]
                            else:
                                laheads = self.grammar.Follow[p.name]
                            for a in laheads:
                                if self.lr_method == 'LALR':
                                    self.automaton_kernel[st][p.number][1].append(a)
                                actlist.append((a,p,"reduce using rule %d (%s)" % (p.number,p)))
                                r = st_action.get(a,None)
                                if r is not None:
                                    # Whoa. Have a shift/reduce or reduce/reduce conflict
                                    if r > 0:
                                        # Need to decide on shift or reduce here
                                        # By default we favor shifting. Need to add
                                        # some precedence rules here.
                                        sprec,slevel = Productions[st_actionp[a].number].prec
                                        rprec,rlevel = Precedence.get(a,('right',0))
                                        if (slevel < rlevel) or ((slevel == rlevel) and (rprec == 'left')):
                                            # We really need to reduce here.
                                            st_action[a] = -p.number
                                            st_actionp[a] = p
                                            if not slevel and not rlevel:
                                                log.info("  ! shift/reduce conflict for %s resolved as reduce",a)
                                                self.sr_conflicts.append((st,a,'reduce'))
                                            Productions[p.number].reduced += 1
                                        elif (slevel == rlevel) and (rprec == 'nonassoc'):
                                            st_action[a] = None
                                        else:
                                            # Hmmm. Guess we'll keep the shift
                                            if not rlevel:
                                                log.info("  ! shift/reduce conflict for %s resolved as shift",a)
                                                self.sr_conflicts.append((st,a,'shift'))
                                    elif r < 0:
                                        # Reduce/reduce conflict.   In this case, we favor the rule
                                        # that was defined first in the grammar file
                                        oldp = Productions[-r]
                                        pp = Productions[p.number]
                                        if oldp.line > pp.line:
                                            st_action[a] = -p.number
                                            st_actionp[a] = p
                                            chosenp,rejectp = pp,oldp
                                            Productions[p.number].reduced += 1
                                            Productions[oldp.number].reduced -= 1
                                        else:
                                            chosenp,rejectp = oldp,pp
                                        self.rr_conflicts.append((st,chosenp,rejectp))
                                        log.info("  ! reduce/reduce conflict for %s resolved using rule %d (%s)", a,st_actionp[a].number, st_actionp[a])
                                    else:
                                        raise LALRError("Unknown conflict in state %d" % st)
                                else:
                                    st_action[a] = -p.number
                                    st_actionp[a] = p
                                    Productions[p.number].reduced += 1
                    else:
                        i = p.lr_index
                        a = p.prod[i+1]       # Get symbol right after the "."
                        if a in self.grammar.Terminals:
                            g = self.lr0_goto(I,a)
                            j = self.lr0_cidhash.get(id(g),-1)
                            if j >= 0:
                                # We are in a shift state
                                actlist.append((a,p,"shift and go to state %d" % j))
                                r = st_action.get(a,None)
                                if r is not None:
                                    # Whoa have a shift/reduce or shift/shift conflict
                                    if r > 0:
                                        if r != j:
                                            raise LALRError("Shift/shift conflict in state %d" % st)
                                    elif r < 0:
                                        # Do a precedence check.
                                        #   -  if precedence of reduce rule is higher, we reduce.
                                        #   -  if precedence of reduce is same and left assoc, we reduce.
                                        #   -  otherwise we shift
                                        rprec,rlevel = Productions[st_actionp[a].number].prec
                                        sprec,slevel = Precedence.get(a,('right',0))
                                        if (slevel > rlevel) or ((slevel == rlevel) and (rprec == 'right')):
                                            # We decide to shift here... highest precedence to shift
                                            Productions[st_actionp[a].number].reduced -= 1
                                            st_action[a] = j
                                            st_actionp[a] = p
                                            if not rlevel:
                                                log.info("  ! shift/reduce conflict for %s resolved as shift",a)
                                                self.sr_conflicts.append((st,a,'shift'))
                                        elif (slevel == rlevel) and (rprec == 'nonassoc'):
                                            st_action[a] = None
                                        else:
                                            # Hmmm. Guess we'll keep the reduce
                                            if not slevel and not rlevel:
                                                log.info("  ! shift/reduce conflict for %s resolved as reduce",a)
                                                self.sr_conflicts.append((st,a,'reduce'))

                                    else:
                                        raise LALRError("Unknown conflict in state %d" % st)
                                else:
                                    st_action[a] = j
                                    st_actionp[a] = p

            # Print the actions associated with each terminal
            _actprint = { }
            for a,p,m in actlist:
                if a in st_action:
                    if p is st_actionp[a]:
                        log.info("    %-15s %s",a,m)
                        _actprint[(a,m)] = 1
            log.info("")
            # Print the actions that were not used. (debugging)
            not_used = 0
            for a,p,m in actlist:
                if a in st_action:
                    if p is not st_actionp[a]:
                        if not (a,m) in _actprint:
                            log.debug("  ! %-15s [ %s ]",a,m)
                            not_used = 1
                            _actprint[(a,m)] = 1
            if not_used:
                log.debug("")

            # Construct the goto table for this state

            nkeys = { }
            for ii in I:
                for s in ii.usyms:
                    if s in self.grammar.Nonterminals:
                        nkeys[s] = None
            for n in nkeys:
                g = self.lr0_goto(I,n)
                j = self.lr0_cidhash.get(id(g),-1)
                if j >= 0:
                    st_goto[n] = j
                    log.info("    %-30s shift and go to state %d",n,j)

            action[st] = st_action
            actionp[st] = st_actionp
            goto[st] = st_goto
            st += 1
