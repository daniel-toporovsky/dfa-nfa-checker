from __future__ import annotations

import os

"""automata.py –Minimal OOP helper‑library for playing with DFA/NFA in the terminal.

Features
========
*   Build a DFA or NFA by giving the classic 5‑tuple (Q, Σ, δ, q₀, F).
*   Run a word and pretty‑print the execution trace + final verdict.
*   Brute‑force correctness checker: compare the automaton with a boolean
    specification on **all** words of length≤15 over its alphabet.
*   ASCII drawing that highlights the start arrow, double‑circle accept
    states, and labelled transitions (ε supported).

No third‑party dependencies –standard library only.
"""
from typing import Dict, Set, Iterable, Callable
import itertools
import subprocess, shutil


__all__ = [
    "Automaton",
    "DFA",
    "NFA",
]

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _all_words(sigma: Set[str], *, max_len: int) -> Iterable[str]:
    """Generate every word over *sigma* up to *max_len* (inclusive)."""
    sigma_sorted = sorted(sigma)
    for length in range(max_len + 1):
        for tup in itertools.product(sigma_sorted, repeat=length):
            yield "".join(tup)


# ---------------------------------------------------------------------------
# Core base‑class
# ---------------------------------------------------------------------------

class Automaton:
    """Abstract base‑class shared by DFA and NFA."""

    EPSILON = "ε"  # use this literal in δ‑tables for ε‑moves

    def __init__(
        self,
        Q: Set[str],
        sigma: Set[str],
        delta: Dict[str, Dict[str, Set[str]]],
        q0: str,
        F: Set[str],
    ) -> None:
        self.Q: Set[str] = set(Q)
        self.sigma: Set[str] = set(sigma)
        self.delta: Dict[str, Dict[str, Set[str]]] = {
            q: {a: set(ns) for a, ns in trans.items()} for q, trans in delta.items()
        }
        self.q0: str = q0
        self.F: Set[str] = set(F)
        self._validate()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def draw(self) -> None:
        """Pretty ASCII dump of the automaton."""
        def fmt_state(s: str) -> str:
            inner = f"*{s}*" if s in self.F else s
            return f"[{inner}]"

        print("AUTOMATON DIAGRAM (ASCII)")
        print("start →", fmt_state(self.q0))
        for q in sorted(self.Q):
            for a, dests in sorted(self.delta.get(q, {}).items()):
                for d in sorted(dests):
                    arrow = "-ε→" if a == self.EPSILON else f"-{a}→"
                    print(f"  {fmt_state(q)} {arrow} {fmt_state(d)}")
        print()

    # Must be implemented by subclasses
    # ------------------------------------------------------------------

    def run(self, word: str, *, verbose: bool = True) -> bool:
        raise NotImplementedError

    # Brute‑force spec checker
    # ------------------------------------------------------------------

    def test_against(self, spec: Callable[[str], bool], *, max_len: int = 15) -> bool:
        """Return *True* iff the automaton matches *spec* on ALL words ≤ *max_len*."""
        ok = True
        for w in _all_words(self.sigma, max_len=max_len):
            aut_ans = self.run(w, verbose=False)
            spec_ans = spec(w)
            if aut_ans != spec_ans:
                print(f"❌ Mismatch on word '{w or 'ε'}': automaton={aut_ans}, spec={spec_ans}")
                ok = False
        if ok:
            print("✅ Automaton matches the specification on all tested words!")
        return ok

    # --------------------------------------------------------------------
    # Pretty Graphviz rendering to the terminal (robust version)
    # --------------------------------------------------------------------
    def draw_graph_easy(self, *, unicode: bool = False) -> None:
        """
        Pretty-print the automaton via Graph::Easy.

        :param unicode: If True, use Unicode box-drawing (--as=boxart);
                        otherwise use pure ASCII (--as=ascii).
        """
        # 1) Build DOT source
        from graphviz import Digraph
        g = Digraph(engine="dot")
        g.attr(rankdir="LR", margin="0.1")
        g.node("__start__", shape="point")
        g.edge("__start__", self.q0, label="")
        for q in self.Q:
            g.node(q, shape="doublecircle" if q in self.F else "circle")
        for src, trans in self.delta.items():
            for sym, dests in trans.items():
                lbl = sym if sym != self.EPSILON else "ε"
                for dst in dests:
                    g.edge(src, dst, label=lbl)
        dot_src = g.source.encode("utf-8")

        # 2) Locate the CLI
        ge = shutil.which("graph-easy")
        if not ge:
            print("⚠ graph-easy not found; falling back to simple draw()")
            return self.draw()

        # 3) Pick the correct --as= flag
        mode = "boxart" if unicode else "ascii"
        cmd = [ge, "--from=dot", f"--as={mode}"]

        # 4) Ensure local Perl5 modules are visible
        env = os.environ.copy()
        home = os.path.expanduser("~")
        env["PERL5LIB"] = f"{home}/perl5/lib/perl5" + (":" + env.get("PERL5LIB", ""))

        # 5) Run it, piping in the DOT
        try:
            p = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )
            out, err = p.communicate(input=dot_src, timeout=5)
            if p.returncode != 0:
                raise subprocess.CalledProcessError(p.returncode, cmd, output=out, stderr=err)
            print(out.decode("utf-8"))
        except subprocess.CalledProcessError as e:
            print(f"⚠ graph-easy failed (exit {e.returncode}):\n{e.stderr.decode()}")
            print("→ falling back to simple draw()")
            self.draw()
        except subprocess.TimeoutExpired:
            print("⚠ graph-easy timed out; falling back to simple draw()")
            self.draw()
    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _validate(self) -> None:
        if self.q0 not in self.Q:
            raise ValueError("Start state q₀ must be in Q")
        if not self.F.issubset(self.Q):
            raise ValueError("Accepting set F must be subset of Q")
        for q, trans in self.delta.items():
            if q not in self.Q:
                raise ValueError(f"Transition defined for unknown state {q}")
            for a, dests in trans.items():
                if a != self.EPSILON and a not in self.sigma:
                    raise ValueError(f"Symbol '{a}' not in alphabet Σ")
                unknown = dests - self.Q
                if unknown:
                    raise ValueError(f"Unknown destination states {unknown}")


# ---------------------------------------------------------------------------
# DFA implementation
# ---------------------------------------------------------------------------

class DFA(Automaton):
    """Deterministic finite automaton."""

    def run(self, word: str, *, verbose: bool = True) -> bool:  # type: ignore[override]
        state = self.q0
        if verbose:
            print(f"RUN DFA on '{word or 'ε'}':")
            print(f"  start at {state}")
        for ch in word:
            if ch not in self.sigma:
                raise ValueError(f"symbol '{ch}' not in alphabet Σ")
            state = next(iter(self.delta[state][ch]))  # deterministic: set of size 1
            if verbose:
                print(f"   -{ch}→ {state}")
        if verbose:
            verdict = "ACCEPT" if state in self.F else "REJECT"
            print(f"  halt at {state}  ⇒  {verdict}\n")
        return state in self.F


# ---------------------------------------------------------------------------
# NFA implementation (ε‑moves allowed)
# ---------------------------------------------------------------------------

class NFA(Automaton):
    """Nondeterministic finite automaton with ε‑transitions."""

    def _eps_closure(self, states: Set[str]) -> Set[str]:
        stack = list(states)
        closure = set(states)
        while stack:
            s = stack.pop()
            for nxt in self.delta.get(s, {}).get(self.EPSILON, set()):
                if nxt not in closure:
                    closure.add(nxt)
                    stack.append(nxt)
        return closure

    def run(self, word: str, *, verbose: bool = True) -> bool:  # type: ignore[override]
        cur: Set[str] = self._eps_closure({self.q0})
        if verbose:
            print(f"RUN NFA on '{word or 'ε'}':")
            print(f"  start ε‑closure = {sorted(cur)}")
        for ch in word:
            if ch not in self.sigma:
                raise ValueError(f"symbol '{ch}' not in alphabet Σ")
            nxt_states: Set[str] = set()
            for s in cur:
                nxt_states.update(self.delta.get(s, {}).get(ch, set()))
            cur = self._eps_closure(nxt_states)
            if verbose:
                print(f"   -{ch}→ ε‑closure = {sorted(cur)}")
        accept = any(s in self.F for s in cur)
        if verbose:
            verdict = "ACCEPT" if accept else "REJECT"
            print(f"  halt in {sorted(cur)}  ⇒  {verdict}\n")
        return accept
