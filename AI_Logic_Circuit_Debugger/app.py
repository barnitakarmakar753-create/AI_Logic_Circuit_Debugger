import streamlit as st
import pandas as pd
import time
from dotenv import load_dotenv

load_dotenv()

from circuit_checker import (
    generate_truth_table,
    compare_truth_tables,
    suggest_basic_correction,
    analyze_verilog_code,
    generate_corrected_verilog,
    verify_corrected_verilog,
    diagnose_gate_faults
)

from ai_agent import (
    get_ai_explanation,
    get_rule_based_explanation,
    format_gate_repairs
)


st.set_page_config(
    page_title="AI Logic Circuit Debugger",
    page_icon="🔌",
    layout="wide"
)


# DASHBOARD DESIGN

st.markdown("""
<style>
.stApp {
    background-color: #f4f7fc;
}

.block-container {
    padding-top: 2rem;
    max-width: 1250px;
}

.hero {
    padding: 32px;
    border-radius: 18px;
    background: linear-gradient(120deg, #10284f, #2362a8);
    color: white;
    margin-bottom: 22px;
    box-shadow: 0 8px 25px rgba(16, 40, 79, 0.15);
}

.hero h1 {
    color: white;
    font-size: 32px;
    font-weight: 750;
    margin-bottom: 8px;
}

.hero p {
    color: #e4efff;
    font-size: 15px;
    margin-bottom: 0;
}

.hero-tags {
    margin-top: 18px;
}

.hero-tag {
    display: inline-block;
    background: rgba(255,255,255,0.13);
    color: white;
    padding: 7px 12px;
    border-radius: 20px;
    margin: 4px;
    font-size: 12px;
    border: 1px solid rgba(255,255,255,0.2);
}

.section-title {
    color: #17345f;
    font-size: 22px;
    font-weight: 700;
    margin-top: 12px;
    margin-bottom: 15px;
}

.small-note {
    color: #65748b;
    font-size: 0.9rem;
}

div[data-testid="stMetric"] {
    background: white;
    padding: 18px;
    border-radius: 14px;
    border: 1px solid #e1e8f0;
    box-shadow: 0 3px 12px rgba(15, 35, 75, 0.04);
}

.stButton > button {
    border-radius: 10px;
    font-weight: 650;
    min-height: 45px;
}

.stDownloadButton > button {
    border-radius: 10px;
    font-weight: 600;
}

div[data-testid="stDataFrame"] {
    background: white;
    border-radius: 12px;
}

div[data-testid="stSidebar"] {
    background-color: #ffffff;
}

.footer {
    text-align: center;
    color: #8290a5;
    font-size: 12px;
    padding-top: 12px;
    line-height: 1.8;
}
</style>
""", unsafe_allow_html=True)


# PROJECT HEADER

st.markdown("""
<div class="hero">
    <h1>🔌 AI Logic Circuit Debugger</h1>
    <p><b>Agentic AI for Logic Circuit Debugging</b></p>
    <p>
        Analyse Boolean expressions and Verilog code,
        compare truth tables, detect circuit faults,
        and generate intelligent diagnostic reports.
    </p>
    <div class="hero-tags">
        <span class="hero-tag">Digital Logic Analysis</span>
        <span class="hero-tag">LangChain + Gemini</span>
        <span class="hero-tag">Verilog Analysis</span>
        <span class="hero-tag">Automated Gate Repair</span>
    </div>
</div>
""", unsafe_allow_html=True)


st.info(
    "The debugger checks Boolean expressions and supported "
    "combinational Verilog code against expected behaviour."
)


# SIDEBAR

with st.sidebar:

    st.header("⚙️ Circuit Settings")

    variable_count = st.selectbox(
        "Number of inputs",
        [2, 3, 4],
        index=1
    )

    variable_names = ["A", "B", "C", "D"][:variable_count]

    st.divider()

    st.subheader("AI Connection")

    st.success("Gemini integration configured")

    st.caption(
        "The LangChain agent generates diagnostic explanations "
        "when Gemini is available. A local Python diagnostic "
        "is used as a fallback."
    )

    st.divider()

    st.subheader("Supported Operators")

    st.markdown("""
    - `&` — AND
    - `|` — OR
    - `~` — NOT
    - `^` — XOR
    """)

    st.divider()

    st.caption("Academic Digital Electronics Project | P5")


# AI REQUEST COOLDOWN

if "last_ai_call" not in st.session_state:
    st.session_state["last_ai_call"] = 0


def run_circuit_agent(
    expected_expression,
    actual_expression,
    mismatches,
    verilog_code=None,
    output_signal=None,
    gate_repair_result=None
):
    """Run the LangChain agent with a one-minute request cooldown."""

    current_time = time.time()

    elapsed = current_time - st.session_state["last_ai_call"]

    if elapsed >= 60:

        with st.spinner("LangChain AI agent is analysing the circuit..."):

            explanation, mode = get_ai_explanation(
                expected_expression,
                actual_expression,
                mismatches,
                verilog_code=verilog_code,
                output_signal=output_signal,
                gate_repair_result=gate_repair_result
            )

        st.session_state["last_ai_call"] = time.time()

        return explanation, mode

    explanation = get_rule_based_explanation(
        expected_expression,
        actual_expression,
        mismatches,
        verilog_code,
        gate_repair_result
    )

    return (
        explanation
        + "\n\nThe one-minute API request protection is active. "
        "The local Python diagnostic was used.",
        "Rule-based diagnostic (API cooldown)"
    )


# BOOLEAN EXPRESSION DEBUGGER

st.markdown(
    '<div class="section-title">01 | Boolean Expression Analysis</div>',
    unsafe_allow_html=True
)

st.write(
    "Provide the expected Boolean expression and the actual "
    "expression implemented by your circuit."
)

col1, col2 = st.columns(2)

with col1:

    st.markdown("**Expected Boolean Expression**")

    expected_expression = st.text_input(
        "Expected expression",
        value="A & B",
        key="expected_expression"
    )

with col2:

    st.markdown("**Actual Circuit Expression**")

    actual_expression = st.text_input(
        "Actual expression",
        value="A | B",
        key="actual_expression"
    )

st.markdown(
    '<p class="small-note">Operators: & = AND, | = OR, '
    '~ = NOT, ^ = XOR. Example: (A & B) | ~C.</p>',
    unsafe_allow_html=True
)


if st.button(
    "🔍 Debug Boolean Circuit",
    type="primary",
    use_container_width=True
):

    try:

        expected_rows = generate_truth_table(
            expected_expression,
            variable_names
        )

        actual_rows = generate_truth_table(
            actual_expression,
            variable_names
        )

        mismatches = compare_truth_tables(
            expected_rows,
            actual_rows,
            variable_names
        )

        st.session_state["debug_result"] = {
            "expected_rows": expected_rows,
            "actual_rows": actual_rows,
            "mismatches": mismatches,
            "expected_expression": expected_expression,
            "actual_expression": actual_expression,
            "variables": variable_names
        }

        if not mismatches:

            explanation = (
                "Both circuits produce identical outputs for every "
                "input combination. No functional fault was detected."
            )

            mode = "Python truth-table verification"

        else:

            explanation, mode = run_circuit_agent(
                expected_expression,
                actual_expression,
                mismatches
            )

        st.session_state["explanation"] = explanation
        st.session_state["mode"] = mode

    except ValueError as error:

        st.error(str(error))

    except Exception as error:

        st.error(f"Unexpected error: {error}")


# BOOLEAN RESULTS

if "debug_result" in st.session_state:

    result = st.session_state["debug_result"]

    expected_rows = result["expected_rows"]
    actual_rows = result["actual_rows"]
    mismatches = result["mismatches"]
    variables = result["variables"]

    st.divider()

    st.markdown(
        '<div class="section-title">02 | Boolean Analysis Overview</div>',
        unsafe_allow_html=True
    )

    metric1, metric2, metric3 = st.columns(3)

    metric1.metric("Total Test Cases", len(expected_rows))
    metric2.metric("Mismatched Rows", len(mismatches))

    metric3.metric(
        "Circuit Status",
        "PASS" if not mismatches else "FAULT DETECTED"
    )

    if not mismatches:

        st.success(
            "✓ The expected and actual circuits are functionally equivalent."
        )

    else:

        st.error(
            "⚠ Functional mismatch detected. The circuit requires correction."
        )

    st.divider()

    st.markdown(
        '<div class="section-title">03 | Truth Table Comparison</div>',
        unsafe_allow_html=True
    )

    table_rows = []

    for expected, actual in zip(expected_rows, actual_rows):

        row = {
            name: expected[name]
            for name in variables
        }

        row["Expected Output"] = expected["Output"]
        row["Actual Output"] = actual["Output"]

        row["Status"] = (
            "✓ Match"
            if expected["Output"] == actual["Output"]
            else "✗ Mismatch"
        )

        table_rows.append(row)

    st.dataframe(
        pd.DataFrame(table_rows),
        use_container_width=True,
        hide_index=True
    )

    if mismatches:

        with st.expander("View Detailed Mismatched Rows", expanded=True):

            st.dataframe(
                pd.DataFrame(mismatches),
                use_container_width=True,
                hide_index=True
            )

    st.divider()

    st.markdown(
        '<div class="section-title">04 | AI Debugging Report</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Diagnosis mode: "
        + st.session_state.get("mode", "Python diagnostic")
    )

    with st.container(border=True):

        st.markdown("### 🧠 Diagnostic Explanation")

        st.write(
            st.session_state.get(
                "explanation",
                "No explanation available."
            )
        )

    st.markdown("### 🛠 Suggested Correction")

    with st.container(border=True):

        st.write(
            suggest_basic_correction(
                result["expected_expression"],
                result["actual_expression"],
                mismatches
            )
        )

    st.divider()

    st.markdown(
        '<div class="section-title">05 | Export Boolean Report</div>',
        unsafe_allow_html=True
    )

    csv_data = pd.DataFrame(table_rows).to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "⬇ Download Comparison as CSV",
        data=csv_data,
        file_name="logic_circuit_debug_report.csv",
        mime="text/csv",
        use_container_width=True
    )


# VERILOG CODE ANALYSIS

st.divider()

st.markdown(
    '<div class="section-title">06 | Verilog Code Analysis</div>',
    unsafe_allow_html=True
)

st.write(
    "Enter Verilog code to identify its module, input signals, "
    "output signals, logic expressions and gate structure."
)

verilog_code = st.text_area(
    "Enter Verilog Code",
    value="""module logic_test(A, B, C, Y);
input A, B, C;
output Y;
wire W;

assign W = A & B;
assign Y = W & C;

endmodule""",
    height=220,
    key="verilog_code"
)

expected_verilog_expression = st.text_input(
    "Expected Boolean Behaviour",
    value="(A & B) | C",
    key="expected_verilog_expression"
)


# ANALYSE VERILOG BUTTON

if st.button(
    "🔬 Analyse Verilog Code",
    type="primary",
    use_container_width=True
):

    try:

        verilog_result = analyze_verilog_code(verilog_code)

        st.session_state["verilog_result"] = verilog_result

        # Clear previous results when source code changes.
        for key in [
            "verilog_comparison",
            "verilog_ai_report",
            "verilog_ai_mode",
            "verilog_ai_key",
            "gate_repair_result",
            "corrected_verilog",
            "corrected_verification"
        ]:
            st.session_state.pop(key, None)

        st.success("Verilog code analysed successfully.")

    except Exception as error:

        st.error(f"Verilog analysis failed: {error}")


# DISPLAY VERILOG ANALYSIS

if "verilog_result" in st.session_state:

    verilog_result = st.session_state["verilog_result"]

    st.markdown("### Verilog Analysis Results")

    st.write("**Module Name:**", verilog_result["module_name"])

    st.write(
        "**Input Signals:**",
        ", ".join(verilog_result["inputs"])
    )

    st.write(
        "**Output Signals:**",
        ", ".join(verilog_result["outputs"])
    )

    st.markdown("### Extracted Boolean Expressions")

    st.json(verilog_result["expressions"])

    # Display extracted gate structure.

    if "gates" in verilog_result:

        st.markdown("### Extracted Gate Structure")

        st.metric(
            "Total Extracted Gates",
            verilog_result.get("gate_count", len(verilog_result["gates"]))
        )

        st.dataframe(
            pd.DataFrame(verilog_result["gates"]),
            use_container_width=True,
            hide_index=True
        )

    selected_output = st.selectbox(
        "Select output to verify",
        verilog_result["outputs"],
        key="selected_verilog_output"
    )

    if st.button(
        "Compare Verilog with Expected Behaviour",
        use_container_width=True
    ):

        try:

            input_signals = verilog_result["inputs"]

            expected_rows = generate_truth_table(
                expected_verilog_expression,
                input_signals
            )

            actual_rows = verilog_result["truth_tables"][
                selected_output
            ]

            mismatches = compare_truth_tables(
                expected_rows,
                actual_rows,
                input_signals
            )

            # Run the structural gate-repair engine.

            gate_repair_result = diagnose_gate_faults(
                verilog_code,
                expected_verilog_expression,
                selected_output
            )

            st.session_state["verilog_comparison"] = {
                "expected_rows": expected_rows,
                "actual_rows": actual_rows,
                "mismatches": mismatches,
                "expected_expression": expected_verilog_expression,
                "actual_expression": verilog_result["expressions"][
                    selected_output
                ],
                "inputs": input_signals,
                "output": selected_output,
                "source_code": verilog_code,
                "gate_repair_result": gate_repair_result
            }

            st.session_state["gate_repair_result"] = gate_repair_result

            # Clear old AI and correction results.

            for key in [
                "verilog_ai_report",
                "verilog_ai_mode",
                "verilog_ai_key",
                "corrected_verilog",
                "corrected_verification"
            ]:
                st.session_state.pop(key, None)

            st.success(
                "Truth-table comparison and automated gate diagnosis completed."
            )

        except Exception as error:

            st.error(f"Comparison or gate diagnosis failed: {error}")


# DISPLAY VERILOG COMPARISON

if "verilog_comparison" in st.session_state:

    comparison = st.session_state["verilog_comparison"]

    expected_rows = comparison["expected_rows"]
    actual_rows = comparison["actual_rows"]
    mismatches = comparison["mismatches"]
    input_signals = comparison["inputs"]

    st.divider()

    st.markdown("### Verilog Truth Table Comparison")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Test Cases", len(expected_rows))
    col2.metric("Mismatched Rows", len(mismatches))

    col3.metric(
        "Circuit Status",
        "PASS" if not mismatches else "FAULT DETECTED"
    )

    if not mismatches:

        st.success(
            "✓ Verilog output matches the expected behaviour."
        )

    else:

        st.error(
            "⚠ Verilog output differs from expected behaviour."
        )

    table_rows = []

    for expected, actual in zip(expected_rows, actual_rows):

        row = {
            name: expected[name]
            for name in input_signals
        }

        row["Expected Output"] = expected["Output"]
        row["Actual Output"] = actual["Output"]

        row["Status"] = (
            "✓ Match"
            if expected["Output"] == actual["Output"]
            else "✗ Mismatch"
        )

        table_rows.append(row)

    st.dataframe(
        pd.DataFrame(table_rows),
        use_container_width=True,
        hide_index=True
    )

    if mismatches:

        with st.expander("View Faulty Truth Table Rows", expanded=True):

            st.dataframe(
                pd.DataFrame(mismatches),
                use_container_width=True,
                hide_index=True
            )

    # AUTOMATED GATE FAULT DIAGNOSIS

    st.divider()

    st.markdown(
        "### 07 | Automated Gate Fault Diagnosis"
    )

    st.write(
        "The repair engine examines the extracted gate network "
        "and searches for gate-type replacements that make the "
        "circuit match the expected truth table."
    )

    gate_repair_result = comparison.get("gate_repair_result", {})

    repair_status = gate_repair_result.get("status", "UNKNOWN")
    candidates = gate_repair_result.get("candidates", [])

    faults_found = gate_repair_result.get("faults_found", 0)

    repair_col1, repair_col2, repair_col3 = st.columns(3)

    repair_col1.metric(
        "Faulty Gates Identified",
        faults_found
    )

    repair_col2.metric(
        "Repair Candidates",
        len(candidates)
    )

    repair_col3.metric(
        "Verification",
        "PASS" if any(
            candidate.get("verified", False)
            for candidate in candidates
        ) else "NOT VERIFIED"
    )

    if repair_status == "NO_FAULT":

        st.success(
            "No gate replacement is required. "
            "The original circuit already matches the expected behaviour."
        )

    elif repair_status == "REPAIR_FOUND":

        st.success(
            "A gate replacement solution was found and verified "
            "against the expected truth table."
        )

        for index, candidate in enumerate(candidates, start=1):

            st.markdown(
                f"#### Repair Candidate {index}"
            )

            repair_rows = []

            for repair in candidate.get("repairs", []):

                repair_rows.append({
                    "Gate ID": repair.get("gate_id"),
                    "Output": repair.get("output"),
                    "Inputs": ", ".join(repair.get("inputs", [])),
                    "Original Gate": repair.get("original_type"),
                    "Suggested Gate": repair.get("suggested_type"),
                    "Correction": repair.get("repair")
                })

            if repair_rows:

                st.dataframe(
                    pd.DataFrame(repair_rows),
                    use_container_width=True,
                    hide_index=True
                )

            if candidate.get("verified", False):

                st.success(
                    "✓ The suggested gate replacements pass "
                    "the Python truth-table verification."
                )

            else:

                st.warning(
                    "This candidate has not passed verification."
                )

    elif repair_status == "NO_REPAIR_FOUND":

        st.warning(
            "No valid gate-type replacement was found within "
            "the repair engine's current search limits."
        )

    else:

        st.warning(
            "The repair engine did not return a recognised repair status."
        )

    st.caption(
        "This repair search changes gate types while preserving "
        "the existing connections. It does not currently search "
        "for wiring or connection changes."
    )

    # LANGCHAIN VERILOG DIAGNOSIS

    st.divider()

    st.markdown("### 08 | LangChain Verilog Diagnosis")

    if mismatches:

        current_ai_key = (
            comparison["expected_expression"],
            comparison["actual_expression"],
            comparison["source_code"],
            comparison["output"]
        )

        if (
            "verilog_ai_report" not in st.session_state
            or st.session_state.get("verilog_ai_key") != current_ai_key
        ):

            explanation, mode = run_circuit_agent(
                comparison["expected_expression"],
                comparison["actual_expression"],
                mismatches,
                verilog_code=comparison["source_code"],
                output_signal=comparison["output"],
                gate_repair_result=gate_repair_result
            )

            st.session_state["verilog_ai_report"] = explanation
            st.session_state["verilog_ai_mode"] = mode
            st.session_state["verilog_ai_key"] = current_ai_key

        st.caption(
            "Diagnosis mode: "
            + st.session_state["verilog_ai_mode"]
        )

        with st.container(border=True):

            st.write(st.session_state["verilog_ai_report"])

    else:

        st.success(
            "No fault detected. The Verilog circuit already matches "
            "the expected truth table."
        )

    # AUTOMATIC CORRECTION

    st.divider()

    st.markdown("### 09 | Corrected Verilog Generation")

    st.write(
        "Generate a corrected Verilog implementation using the "
        "expected Boolean expression. This generates a direct "
        "Boolean assignment, not a physical gate-by-gate netlist."
    )

    if st.button(
        "🛠 Generate and Verify Corrected Verilog",
        type="primary",
        use_container_width=True
    ):

        try:

            corrected_code = generate_corrected_verilog(
                comparison["expected_expression"],
                input_signals,
                comparison["output"],
                module_name="corrected_logic"
            )

            verification = verify_corrected_verilog(
                corrected_code,
                comparison["expected_expression"],
                comparison["output"]
            )

            st.session_state["corrected_verilog"] = corrected_code
            st.session_state["corrected_verification"] = verification

        except Exception as error:

            st.error(f"Correction generation failed: {error}")

    # DISPLAY CORRECTION

    if "corrected_verilog" in st.session_state:

        corrected_code = st.session_state["corrected_verilog"]

        verification = st.session_state["corrected_verification"]

        st.markdown("#### Generated Corrected Verilog Code")

        st.code(
            corrected_code,
            language="verilog"
        )

        st.download_button(
            "⬇ Download Corrected Verilog",
            data=corrected_code,
            file_name="corrected_logic.v",
            mime="text/plain",
            use_container_width=True
        )

        st.markdown("#### Corrected Circuit Verification")

        verify_col1, verify_col2 = st.columns(2)

        verify_col1.metric(
            "Corrected Test Cases",
            len(verification["expected_rows"])
        )

        verify_col2.metric(
            "Remaining Mismatches",
            len(verification["mismatches"])
        )

        if verification["passed"]:

            st.success(
                "✓ PASS: The generated corrected Verilog matches "
                "the expected truth table for every input combination."
            )

        else:

            st.error(
                "FAULT DETECTED: The generated corrected Verilog "
                "still contains mismatched outputs."
            )

        st.markdown("#### Corrected Truth Table")

        corrected_rows = []

        for expected, actual in zip(
            verification["expected_rows"],
            verification["actual_rows"]
        ):

            row = {
                name: expected[name]
                for name in input_signals
            }

            row["Expected Output"] = expected["Output"]
            row["Corrected Output"] = actual["Output"]

            row["Status"] = (
                "✓ Match"
                if expected["Output"] == actual["Output"]
                else "✗ Mismatch"
            )

            corrected_rows.append(row)

        st.dataframe(
            pd.DataFrame(corrected_rows),
            use_container_width=True,
            hide_index=True
        )

    # EXPORT VERILOG COMPARISON

    st.divider()

    st.markdown("### 10 | Export Verilog Analysis")

    verilog_csv = pd.DataFrame(table_rows).to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "⬇ Download Verilog Analysis as CSV",
        data=verilog_csv,
        file_name="verilog_debug_report.csv",
        mime="text/csv",
        use_container_width=True
    )


# FOOTER

st.divider()

st.markdown("""
<div class="footer">
    <b>Agentic AI for Logic Circuit Debugging</b><br>
    Digital Electronics Project | P5<br>
    Academic Prototype
</div>
""", unsafe_allow_html=True)