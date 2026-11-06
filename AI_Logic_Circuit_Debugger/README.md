#  AI Logic Circuit Debugger
### Agentic AI for Logic Circuit Debugging

An intelligent, Python-based digital logic debugging application that analyses Boolean expressions and supported Verilog code, detects logic errors, identifies faulty gates, suggests gate-level corrections, and verifies proposed repairs using truth-table comparison.

**Project Type:** Academic Digital Electronics Project  
**Project Category:** P5  
**Core Technologies:** Python, Streamlit, LangChain, Google Gemini, Pandas

---

##  1. Project Overview

The **AI Logic Circuit Debugger** is designed to simplify the process of identifying and correcting errors in digital logic circuits.

In traditional digital circuit debugging, students and developers may need to manually construct truth tables, compare expected and actual outputs, and identify incorrect logic gates. This process can become time-consuming, especially when circuits contain multiple gates and intermediate connections.

This project provides an automated approach to digital logic debugging.

Users can enter expected and actual Boolean expressions or provide supported combinational Verilog code. The application generates truth tables, compares outputs, identifies mismatches, analyses gate structures, suggests possible gate replacements, and verifies whether the proposed corrections produce the expected behaviour.

The application also integrates a LangChain-based AI agent with Google Gemini for diagnostic explanations. When the external AI service is unavailable or its quota is exhausted, a local rule-based explanation system provides fallback diagnostics.

---

##  2. Project Objectives

- Analyse expected and actual Boolean expressions.
- Generate truth tables automatically.
- Detect mismatches between expected and actual circuit outputs.
- Analyse supported combinational Verilog code.
- Extract intermediate wires and gate-level structures.
- Identify potentially faulty logic gates.
- Suggest corrected gate combinations.
- Generate corrected Verilog code for supported repairs.
- Verify proposed repairs through truth-table comparison.
- Provide AI-assisted diagnostic explanations.
- Export debugging results as CSV reports.

---

##  3. Main Features

### A. Boolean Expression Analysis

- Accepts expected and actual Boolean expressions.
- Supports AND (`&`), OR (`|`), NOT (`~`), and XOR (`^`).
- Supports parentheses and Boolean constants `0` and `1`.
- Validates expressions and checks variable names.
- Generates complete truth tables automatically.

### B. Truth Table Comparison

- Compares expected output with actual output.
- Identifies matching and mismatching rows.
- Displays the total number of test cases.
- Calculates the number of mismatches.
- Reports `PASS` or `FAULT DETECTED`.
- Displays detailed mismatch information.

### C. Verilog Code Analysis

The application analyses a supported subset of combinational Verilog code.

Implemented capabilities include:

- Module name extraction.
- Input and output declaration extraction.
- Wire declaration processing.
- Continuous assignment analysis.
- Intermediate wire resolution.
- Boolean expression extraction.
- Gate structure identification.

Supported gate operations include:

- AND
- OR
- NOT
- NAND
- NOR
- XOR
- XNOR

### D. Structural Gate-Level Diagnosis

The debugger does more than compare final outputs.

It extracts the internal gate structure and assigns identifiers to gates, such as:

- `W_G1`
- `Y_G1`

It analyses the extracted structure and searches for possible gate-type replacements.

For supported cases, it can identify corrections such as:

- AND → OR
- AND → XOR
- Other supported gate-type replacements

The repair process can examine one-gate and two-gate replacement combinations while preserving the existing circuit connections.

### E. Automatic Gate Repair and Verification

The repair engine:

1. Extracts the circuit's gate structure.
2. Compares actual and expected behaviour.
3. Identifies possible faulty gates.
4. Generates candidate gate replacements.
5. Produces corrected Verilog for supported repairs.
6. Re-evaluates the corrected circuit.
7. Confirms whether the proposed repair matches the expected truth table.

A repair is reported as verified only when the verification process succeeds.

### F. LangChain + Google Gemini Integration

The project integrates LangChain with Google's Gemini model to provide AI-assisted diagnostic explanations.

The AI component helps explain:

- Detected logic faults.
- Differences between expected and actual behaviour.
- Possible gate-level corrections.
- Debugging results.

A local rule-based fallback is also implemented. It provides diagnostic explanations when the Gemini API is unavailable or its usage quota is exhausted.

**Important:** Truth-table analysis, structural gate diagnosis, and repair verification are performed by the Python analysis engine and do not depend on the external AI service.

### G. CSV Report Export

The application provides an option to export debugging results as a CSV file.

The exported report includes truth-table information and the corresponding analysis results.

---

##  4. System Architecture

The system is organised into seven main functional modules:

1. **User Interface Module** – Accepts Boolean expressions and Verilog code through Streamlit.
2. **Input Processing and Validation Module** – Validates inputs and prepares expressions or code for analysis.
3. **Truth Table Generation and Evaluation Module** – Generates input combinations and evaluates Boolean outputs.
4. **Verilog Analysis and Gate Extraction Module** – Extracts modules, signals, assignments, wires, and gate structures.
5. **Comparison and Fault Detection Module** – Compares actual behaviour with expected behaviour and identifies mismatches.
6. **Structural Gate Diagnosis and Repair Verification Module** – Searches for gate replacements, generates corrections, and verifies proposed repairs.
7. **LangChain AI Explanation and Report Export Module** – Provides AI-assisted or rule-based explanations and supports CSV report export.

**Overall data flow:**

User Input → Validation → Boolean / Verilog Analysis → Truth Table Comparison → Fault Detection → Gate Diagnosis and Repair Verification → Diagnostic Report

---

##  5. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Interactive web application |
| Pandas | Truth-table and tabular data handling |
| Python AST | Safe parsing of supported Boolean expressions |
| LangChain | AI integration framework |
| Google Gemini | AI-assisted diagnostic explanations |
| python-dotenv | Environment variable management |
| CSV | Debugging report export |

---

##  6. Project Structure

```text
AI_Logic_Circuit_Debugger/
│
├── app.py
│   └── Streamlit application and user interface
│
├── circuit_checker.py
│   └── Boolean analysis, truth tables, Verilog
│       analysis, gate extraction, repair and verification
│
├── ai_agent.py
│   └── LangChain integration, Gemini explanations
│       and rule-based fallback
│
├── requirements.txt
│   └── Project dependencies
│
├── README.md
│   └── Project documentation
│
├── .env.example
│   └── Example environment variable configuration
│
└── .gitignore
    └── Files excluded from Git tracking
```

---

##  7. Testing and Validation

The application was tested using Boolean expressions and Verilog programs with both correct and faulty logic.

### Test 1: Boolean AND versus OR

Expected expression:

```python
A & B
```

Actual expression:

```python
A | B
```

Result:
- Total test cases: 8
- Mismatches: 4
- Status: FAULT DETECTED

### Test 2: NOT Gate Verification

Expected expression:

```python
~A
```

Actual expression:

```python
A
```

Result:
- Total test cases: 8
- Mismatches: 8
- Status: FAULT DETECTED

### Test 3: XOR versus OR

Expected expression:

```python
A ^ B
```

Actual expression:

```python
A | B
```

Result:
- Total test cases: 4
- Mismatches: 2
- Status: FAULT DETECTED

### Test 4: Equivalent Boolean Expressions

Expected and actual expressions were configured to produce equivalent outputs.

Result:
- Mismatches: 0
- Status: PASS

### Test 5: Verilog Intermediate Wire Analysis

The application was tested using a Verilog module containing an intermediate wire:

```verilog
module logic_test(A, B, C, Y);

input A, B, C;
output Y;
wire W;

assign W = A & B;
assign Y = W | C;

endmodule
```

Expected behaviour:

```python
(A & B) | C
```

Result:
- Module name extracted successfully.
- Inputs and output identified.
- Intermediate wire resolved.
- Gate structure extracted.
- Mismatches: 0
- Status: PASS

### Test 6: Single-Gate Automatic Repair

Faulty Verilog:

```verilog
module logic_test(A, B, C, Y);

input A, B, C;
output Y;
wire W;

assign W = A & B;
assign Y = W & C;

endmodule
```

Expected behaviour:

```python
(A & B) | C
```

Detected correction:

```text
Y_G1: AND → OR
```

Result:
- Initial mismatches: 4 out of 8.
- Fault count: 1.
- Repair status: REPAIR_FOUND.
- Verification: TRUE.

### Test 7: Two-Gate Automatic Repair

The repair engine was tested with a circuit requiring two gate-type replacements.

Detected corrections:

```text
W_G1: AND → OR
Y_G1: AND → OR
```

Expected behaviour:

```python
(A | B) | C
```

Result:
- Initial mismatches: 6 out of 8.
- Fault count: 2.
- Repair status: REPAIR_FOUND.
- Verification: TRUE.

### Test 8: Different Gate-Type Replacement

Faulty Verilog:

```verilog
module logic_test(A, B, Y);

input A, B;
output Y;

assign Y = A & B;

endmodule
```

Expected behaviour:

```python
A ^ B
```

Detected correction:

```text
Y_G1: AND → XOR
```

Result:
- Total test cases: 4.
- Initial mismatches: 3.
- Fault count: 1.
- Repair status: REPAIR_FOUND.
- Verification: TRUE.

---

##  8. Results and Discussion

The testing results demonstrate that the application can detect Boolean logic errors, analyse supported combinational Verilog code, identify gate-level structures, and suggest corrections for tested single-gate and two-gate replacement scenarios.

The repair engine validates proposed corrections using truth-table comparison rather than accepting a suggested replacement without verification.

The LangChain and Google Gemini integration provides an additional AI-assisted explanation layer. When the external model is unavailable or its quota is exhausted, the local rule-based fallback continues to provide diagnostic explanations.

The project therefore combines deterministic logic verification with AI-assisted debugging.

---

##  9. Installation and Setup

### Prerequisites

- Python 3.10 or later recommended.
- Git.
- Visual Studio Code or another Python editor.
- Internet connection for installing dependencies and using the Gemini API.

### Step 1: Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/AI-Logic-Circuit-Debugger.git
```

Replace `YOUR-USERNAME` with the GitHub username that owns the repository.

### Step 2: Open the project folder

```bash
cd AI-Logic-Circuit-Debugger
```

### Step 3: Create a virtual environment

Windows:

```powershell
python -m venv .venv
```

### Step 4: Activate the environment

```powershell
.venv\Scripts\activate
```

### Step 5: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 6: Configure the Gemini API key (optional)

Create a `.env` file in the project folder and add the environment variable expected by the current `ai_agent.py` implementation.

For example, if the code reads `GOOGLE_API_KEY`:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

Keep the actual `.env` file private. Never commit it to GitHub.

The application can still use its rule-based fallback when the external AI service is unavailable.

### Step 7: Run the application

```bash
streamlit run app.py
```

The application will normally open at:

```text
http://localhost:8501
```

---

##  10. Using the Application

1. Start the Streamlit application.
2. Open the application in a browser.
3. Enter the expected Boolean expression.
4. Enter the actual Boolean expression.
5. Run the Boolean analysis to inspect the truth table and mismatches.
6. Open the Verilog analysis section.
7. Enter supported combinational Verilog code.
8. Provide the expected output behaviour.
9. Inspect the extracted gate structure and fault diagnosis.
10. Review suggested gate replacements and repair verification.
11. Download the debugging results as a CSV file.

---

##  11. Limitations

- The Verilog analyser supports a defined subset of combinational Verilog, not the complete Verilog language.
- The current implementation focuses on single-bit signals and continuous assignments.
- Sequential circuits, clocked logic, complex behavioural blocks, and advanced Verilog constructs are outside the current scope.
- Automatic repair focuses on supported gate-type replacements while preserving existing circuit connections.
- It does not perform arbitrary circuit rewiring or physical hardware repair.
- AI-generated explanations depend on external API availability and usage quotas.
- Rule-based fallback explanations are available when the AI service cannot be used.

---

##  12. Future Enhancements

Possible future improvements include:

- Support for a wider range of Verilog syntax.
- Sequential circuit analysis.
- More advanced multi-gate repair strategies.
- Automatic circuit rewiring and connection diagnosis.
- Circuit diagram visualisation.
- Integration with digital logic simulation tools.
- More detailed repair explanations.
- Additional AI models and local language models.
- Downloadable PDF debugging reports.

---

##  13. Academic Significance

This project demonstrates the application of programming, digital logic, truth-table verification, Verilog analysis, structural fault diagnosis, and AI-assisted explanation in an integrated debugging tool.

It combines conventional Boolean verification with an automated repair approach, making it useful as an educational demonstration of digital circuit analysis and debugging.

---

##  14. Project Information

**Project Title:** Agentic AI for Logic Circuit Debugging

**Application Name:** AI Logic Circuit Debugger

**Project Category:** P5

**Department:** IT-A

**College:** Institute of  Engineering & Management

**Faculty Guide:** Dr.Kajari Sur

**Developed By:** Barnita Karmakar

##  15. References

- Python Documentation: https://docs.python.org/3/
- Streamlit Documentation: https://docs.streamlit.io/
- LangChain Documentation: https://python.langchain.com/
- Google AI for Developers: https://ai.google.dev/
- Pandas Documentation: https://pandas.pydata.org/docs/
- GitHub Documentation: https://docs.github.com/

---

**AI Logic Circuit Debugger — Detect. Diagnose. Repair. Verify.**
