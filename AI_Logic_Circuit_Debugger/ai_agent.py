import os
import json


def format_gate_repairs(gate_repair_result):
    """Format structural gate-repair results for the diagnostic report."""

    if not gate_repair_result:
        return "No structural gate-repair results were supplied."

    status = gate_repair_result.get("status", "UNKNOWN")
    faults = gate_repair_result.get("faults_found", 0)
    candidates = gate_repair_result.get("candidates", [])

    report = f"""
AUTOMATED GATE REPAIR ANALYSIS

Repair Status: {status}
Faulty Gates Identified: {faults}
Number of Repair Candidates: {len(candidates)}
"""

    if candidates:

        for index, candidate in enumerate(candidates, start=1):

            report += f"\nREPAIR CANDIDATE {index}\n"

            for repair in candidate.get("repairs", []):

                report += f"""
Gate ID: {repair.get('gate_id')}
Output Signal: {repair.get('output')}
Input Signals: {repair.get('inputs')}
Original Gate: {repair.get('original_type')}
Suggested Gate: {repair.get('suggested_type')}
Correction: {repair.get('repair')}
"""

            report += (
                "\nTruth Table Verification: "
                + str(candidate.get("verified", False))
                + "\n"
            )

    else:
        report += "\nNo valid gate replacement candidate was found.\n"

    return report.strip()


def get_rule_based_explanation(
    expected_expression,
    actual_expression,
    mismatches,
    verilog_code=None,
    gate_repair_result=None
):
    count = len(mismatches)

    explanation = f"""
CIRCUIT DEBUGGING REPORT

1. EXPECTED CIRCUIT
Expected Boolean expression:
{expected_expression}

2. ACTUAL CIRCUIT
Actual Boolean expression:
{actual_expression}

3. FAULT DETECTION
The truth-table comparison detected {count} mismatched input combinations.

4. POSSIBLE CAUSE
The circuit may contain an incorrect logic gate,
incorrect gate connection, or incorrect Boolean operation.

5. SUGGESTED CORRECTION
Use the expected Boolean expression as the correction target:

{expected_expression}

6. CONCLUSION
The circuit has a functional mismatch and requires correction.
The mismatch has been verified using Python truth-table comparison.
"""

    expected = expected_expression.replace(" ", "")
    actual = actual_expression.replace(" ", "")

    if expected != actual and mismatches:

        if expected == "A&B" and actual == "A|B":

            explanation += """

GATE-LEVEL ANALYSIS

The expected circuit uses an AND gate, but the actual
circuit uses an OR gate.

An AND gate produces 1 only when both inputs are 1.
An OR gate produces 1 when at least one input is 1.

SUGGESTED GATE CORRECTION:
Replace the OR gate with an AND gate.
"""

        elif expected == "A|B" and actual == "A&B":

            explanation += """

GATE-LEVEL ANALYSIS

The expected circuit uses an OR gate, but the actual
circuit uses an AND gate.

SUGGESTED GATE CORRECTION:
Replace the AND gate with an OR gate.
"""

    if verilog_code:

        explanation += """

VERILOG SOURCE
The original Verilog source was supplied for circuit diagnosis.
The Python parser performed the supported syntax analysis.
"""

    if gate_repair_result:

        explanation += "\n\n" + format_gate_repairs(
            gate_repair_result
        )

    if mismatches:

        explanation += "\n\nVERIFIED MISMATCH DETAILS\n"

        for index, row in enumerate(mismatches[:8], start=1):

            explanation += f"\nCase {index}: {row}"

        if count > 8:

            explanation += (
                f"\n...and {count - 8} additional mismatched cases."
            )

    return explanation.strip()


def get_ai_explanation(
    expected_expression,
    actual_expression,
    mismatches,
    api_key=None,
    verilog_code=None,
    output_signal=None,
    gate_repair_result=None
):
    """
    Run the LangChain Gemini debugging agent.

    Structural gate-repair results are optional so existing
    Boolean debugging calls remain compatible.
    """

    fallback = get_rule_based_explanation(
        expected_expression,
        actual_expression,
        mismatches,
        verilog_code,
        gate_repair_result
    )

    key = (
        os.getenv("GOOGLE_API_KEY")
        or os.getenv("GEMINI_API_KEY")
        or api_key
    )

    if not key:

        return (
            fallback
            + "\n\nGemini API key was not found. "
            "The local Python diagnostic was used.",
            "Rule-based diagnostic"
        )

    try:

        from langchain.agents import create_agent
        from langchain.tools import tool
        from langchain_google_genai import ChatGoogleGenerativeAI

        @tool
        def inspect_circuit_mismatches(
            mismatch_report: str
        ) -> str:
            """Inspect verified truth-table mismatch information."""

            return (
                "Verified mismatch information from the Python checker:\n"
                + mismatch_report
            )

        @tool
        def inspect_verilog_source(
            source_code: str
        ) -> str:
            """Inspect the original Verilog source supplied by the user."""

            if not source_code.strip():

                return "No Verilog source was supplied."

            return (
                "Original Verilog source supplied for analysis:\n"
                + source_code
            )

        @tool
        def inspect_gate_repair_results(
            repair_report: str
        ) -> str:
            """
            Inspect structural gate diagnosis and verified
            gate replacement candidates from the Python engine.
            """

            return (
                "Structural gate-repair results generated by "
                "the Python repair engine:\n"
                + repair_report
            )

        model = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash",
            api_key=key,
            temperature=0
        )

        agent = create_agent(
            model=model,
            tools=[
                inspect_circuit_mismatches,
                inspect_verilog_source,
                inspect_gate_repair_results
            ],
            system_prompt="""
You are an expert digital electronics and logic circuit debugging agent.

Your task is to analyse Boolean expressions, Verilog source code,
truth-table mismatches, and structural gate-repair results.

Follow these rules:

1. Inspect the verified truth-table mismatch information.
2. Inspect the original Verilog source when provided.
3. Inspect the structural gate-repair results when provided.
4. Compare expected and actual circuit behaviour.
5. Identify faulty gates using the supplied gate IDs.
6. Explain the original and suggested gate types.
7. Explain why the suggested replacements correct the circuit.
8. Suggest specific corrected gate combinations.
9. Provide the corrected Boolean expression.
10. Clearly distinguish a suggested repair from a verified repair.
11. Only report a repair as verified if the Python repair engine
    explicitly reports verified=True.
12. Never invent gate IDs, signals, connections, or mismatch rows.
13. Never claim physical hardware was inspected or repaired.
14. Do not claim that connection rewiring was tested when it was not.
15. Explain that equivalent circuits may have multiple valid
    gate implementations.

Use simple, clear language suitable for an academic project.
"""
        )

        mismatch_report = json.dumps(
            mismatches,
            indent=2,
            default=str
        )

        repair_report = format_gate_repairs(
            gate_repair_result
        )

        prompt = f"""
Analyse the following logic circuit.

EXPECTED BOOLEAN EXPRESSION:
{expected_expression}

ACTUAL BOOLEAN EXPRESSION:
{actual_expression}

OUTPUT SIGNAL:
{output_signal or "Not specified"}

NUMBER OF VERIFIED MISMATCHES:
{len(mismatches)}

VERIFIED MISMATCH DATA:
{mismatch_report}

ORIGINAL VERILOG SOURCE:
{verilog_code or "No Verilog source supplied."}

STRUCTURAL GATE REPAIR RESULTS:
{repair_report}

Please use your inspection tools to examine the supplied evidence.

Prepare a debugging report containing:

1. Expected circuit behaviour.
2. Actual circuit behaviour.
3. Explanation of the mismatched outputs.
4. Identified faulty gates and their gate IDs.
5. Original gate types and suggested replacements.
6. Explanation of the suggested gate combinations.
7. Corrected Boolean expression.
8. Whether the Python repair engine verified the candidate.
9. A clear conclusion.

Do not invent repair results.

Do not claim that corrected Verilog code has been generated
or verified unless the supplied evidence explicitly confirms it.
"""

        result = agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        })

        answer = result["messages"][-1].content

        if isinstance(answer, list):

            answer = "\n".join(
                item.get("text", str(item))
                if isinstance(item, dict)
                else str(item)
                for item in answer
            )

        return str(answer), "LangChain Gemini AI agent"

    except Exception as error:

        error_text = str(error).lower()

        if (
            "resource_exhausted" in error_text
            or "quota" in error_text
            or "429" in error_text
        ):

            return (
                fallback
                + "\n\nGemini AI is temporarily unavailable because "
                "the free API quota has been exhausted. "
                "The local Python diagnostic is being used.",
                "Rule-based fallback (Gemini quota exhausted)"
            )

        if "404" in error_text or "not_found" in error_text:

            reason = (
                "The configured Gemini model is currently unavailable."
            )

        else:

            reason = "Gemini could not complete the AI analysis."

        return (
            fallback
            + "\n\n"
            + reason
            + " The local Python diagnostic is being used.",
            "Rule-based fallback"
        )