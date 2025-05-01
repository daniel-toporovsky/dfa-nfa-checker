# DFA/NFA checker

DFA/NFA checker is a Python module for checking your Automata behaviour.

#### The module was created on MacOS, if you prefer to use it on Windows you would have to deal with any issues by yourself :( 

## Visualization
Before using `draw_graph_easy()` function make sure to:

1) Install `cpanm` if you don’t already have it
```bash
brew install cpanminus
```
2) Install the `Graph::Easy CLI`
```bash
sudo cpanm Graph::Easy
cpanm --local-lib=~/perl5 local::lib && eval "$(perl -I ~/perl5/lib/perl5 -Mlocal::lib)"
```

## Quickstart

```python
from automata import DFA, NFA, Automaton

# Define the 5-tuple:
Q     = {"q0", "q1"}
Σ     = {"0", "1"}
δ     = {
    "q0": {"0": {"q1"}, "1": {"q0"}},
    "q1": {"0": {"q0"}, "1": {"q1"}},
}
q0    = "q0"
F     = {"q0"}

# Create a DFA:
even0 = DFA(Q, Σ, δ, q0, F)

# Run it:
even0.run("10100")           # step-by-step trace + ACCEPT/REJECT

# Test against a specification function:
def spec_even0(w: str) -> bool:
    return w.count("0") % 2 == 0

even0.test_against(spec_even0, max_len=8)
# → ✅ Automaton matches the specification on all tested words!
```

## Creating an NFA (with ε-moves)
```python
# 0* 1 (0|1)
Qn = {"s", "mid", "end"}
Σn = {"0", "1"}

δn = {
    "s":   {"0": {"s"}, "1": {"mid"}},               # 0* then 1
    "mid": {Automaton.EPSILON: {"end"}},             # ε-move
    "end": {"0": {"end"}, "1": {"end"}},
}
nfa = NFA(Qn, Σn, δn, "s", {"end"})

nfa.draw()                   # simple ASCII transitions
nfa.run("000101")            # NFA-step trace + ACCEPT/REJECT
nfa.test_against(lambda w: bool(w) and w.startswith("1"), max_len=5)
```
## API Reference
### Class `Automaton`
#### Constructor
```python
Automaton(Q, Σ, δ, q0, F)
```
- `Q: Set[str]` – states
- `Σ: Set[str]` – alphabet symbols
- `δ: Dict[str, Dict[str, Set[str]]]` – transition table.  
Use `Automaton.EPSILON` (the string `"ε"`) for ε-moves
- `q0: str` – start state
- `F: Set[str]` – accepting states

#### Methods
- `draw()`  
Prints a minimal ASCII list of states & transitions.
- `run(word: str, verbose: bool = True) → bool`  
Executes on the input string; prints each step if verbose and returns True if accepted.
- `test_against(spec: Callable[[str], bool], max_len: int = 15) → bool`  
Exhaustively compares the automaton’s behavior to spec(w) for all words of length ≤ max_len. Reports mismatches or a success message.

### Class `DFA(Automaton)`
Same interface as `Automaton`, but enforces that each δ-entry maps to a singleton set.

### Class `NFA(Automaton)`
Supports ε-closure. Same interface as `Automaton`.

## Optional Pretty Rendering

After installing `Graph::Easy`, you get extra methods on your automata:
```python
# ASCII / Unicode via Graph::Easy
dfa.draw_graph_easy(unicode=False)   # pure ASCII (--as=ascii)
nfa.draw_graph_easy(unicode=True)    # Unicode box-drawing (--as=boxart)
```
All of these will fall back to `draw()` if the external tooling is missing or fails.

## Examples

```python
if __name__ == "__main__":
    # Example DFA even-0’s:
    Q = {"q0", "q1"}; Σ = {"0","1"}
    δ = {"q0":{"0":{"q1"},"1":{"q0"}},
         "q1":{"0":{"q0"},"1":{"q1"}}}
    dfa = DFA(Q, Σ, δ, "q0", {"q0"})
    dfa.draw_graph_easy()
    dfa.run("10100")

    # Example NFA for (10|011) · Σ* · (00|11):
    Qn = {"q0","q1","q2","q3","q4","q5","q6","q7"}
    Σn = {"0","1"}
    δn = {
      "q0":{"0":{"q1"},"1":{"q2"}},
      "q1":{"1":{"q3"}},
      "q2":{"0":{"q4"}},
      "q3":{"1":{"q6"}, Automaton.EPSILON:{"q5"}},
      "q4":{"0":{"q6"}, Automaton.EPSILON:{"q5"}},
      "q5":{"0":{"q5"},"1":{"q5"},Automaton.EPSILON:{"q1","q2"}},
      "q6":{Automaton.EPSILON:{"q5"}},
    }
    nfa = NFA(Qn, Σn, δn, "q0", {"q6"})
    nfa.draw_graph_easy(unicode=True)
    nfa.run("011")
    nfa.test_against(lambda w: (w.startswith("10") or w.startswith("011"))
                              and (w.endswith("00") or w.endswith("11")),
                     max_len=6)
```

## Contributing

Just a coffee in Karnaf is enough

## License

[MIT](https://choosealicense.com/licenses/mit/)