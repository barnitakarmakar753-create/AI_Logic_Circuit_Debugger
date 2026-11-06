# AI-Assisted Logic Circuit Debugger (P5)

## Current version
This prototype compares expected and actual Boolean expressions by generating truth tables. It identifies mismatches and provides a basic diagnostic. If an OpenAI API key is supplied, a LangChain agent can produce a more natural explanation.

## Requirements
- Python 3.10 or newer
- Internet connection for package installation
- Optional OpenAI API key for AI explanations

## Windows setup
```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Boolean operators
- `&` = AND
- `|` = OR
- `~` = NOT
- `^` = XOR

Example:
- Expected: `A & B`
- Actual: `A | B`

## Current limitations
- Version 1 compares Boolean expressions for combinational circuits.
- Verilog source parsing, automatic gate-netlist repair, and sequential circuit support are not included yet.
- The AI explanation is optional; deterministic comparison works without an API key.
