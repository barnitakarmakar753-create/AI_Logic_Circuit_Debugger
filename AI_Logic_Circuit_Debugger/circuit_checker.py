
import re
import ast
from itertools import product, combinations


SUPPORTED_GATES = (
    "AND", "OR", "NOT", "NAND", "NOR", "XOR", "XNOR"
)


# --------------------------------------------------
# 1. BOOLEAN EXPRESSION ANALYSIS
# --------------------------------------------------

def parse_boolean_expression(expression, variable_names):
    cleaned = expression.strip()

    if not cleaned:
        raise ValueError("Please enter a Boolean expression.")

    try:
        tree = ast.parse(cleaned, mode="eval")
        node = tree.body

        def validate(item):
            if isinstance(item, ast.Name):
                if item.id not in variable_names:
                    raise ValueError(
                        f"Unknown input variable: {item.id}"
                    )

            elif isinstance(item, ast.Constant):
                if type(item.value) not in (int, bool) or item.value not in (0, 1):
                    raise ValueError(
                        "Only Boolean values 0 and 1 are allowed."
                    )

            elif isinstance(item, ast.BinOp):
                if not isinstance(
                    item.op,
                    (ast.BitAnd, ast.BitOr, ast.BitXor)
                ):
                    raise ValueError("Unsupported Boolean operator.")

                validate(item.left)
                validate(item.right)

            elif isinstance(item, ast.UnaryOp):
                if not isinstance(item.op, ast.Invert):
                    raise ValueError("Unsupported Boolean operator.")

                validate(item.operand)

            else:
                raise ValueError("Invalid Boolean expression.")

        validate(node)
        return node

    except Exception as exc:
        if isinstance(exc, ValueError):
            raise

        raise ValueError(
            "Use &, |, ~, ^ and parentheses. "
            "Example: (A & B) | ~C"
        ) from exc


def evaluate_expression(expression, variable_names, values):
    inputs = {
        name: bool(values[index])
        for index, name in enumerate(variable_names)
    }

    def calculate(node):
        if isinstance(node, ast.Name):
            return inputs[node.id]

        if isinstance(node, ast.Constant):
            return bool(node.value)

        if isinstance(node, ast.UnaryOp):
            return not calculate(node.operand)

        if isinstance(node, ast.BinOp):
            left = calculate(node.left)
            right = calculate(node.right)

            if isinstance(node.op, ast.BitAnd):
                return left and right

            if isinstance(node.op, ast.BitOr):
                return left or right

            if isinstance(node.op, ast.BitXor):
                return left != right

        raise ValueError("Invalid Boolean expression.")

    return int(calculate(expression))


def generate_truth_table(expression_text, variable_names):
    expression = parse_boolean_expression(
        expression_text,
        variable_names
    )

    rows = []

    for values in product([0, 1], repeat=len(variable_names)):
        rows.append({
            **{
                name: values[index]
                for index, name in enumerate(variable_names)
            },
            "Output": evaluate_expression(
                expression,
                variable_names,
                values
            )
        })

    return rows


def compare_truth_tables(expected_rows, actual_rows, variable_names):
    if len(expected_rows) != len(actual_rows):
        raise ValueError(
            "Expected and actual truth tables have different sizes."
        )

    mismatches = []

    for expected, actual in zip(expected_rows, actual_rows):
        if expected["Output"] != actual["Output"]:
            mismatches.append({
                **{
                    name: expected[name]
                    for name in variable_names
                },
                "Expected": expected["Output"],
                "Actual": actual["Output"]
            })

    return mismatches


def suggest_basic_correction(
    expected_expression,
    actual_expression,
    mismatches
):
    if not mismatches:
        return (
            "No correction is required. "
            "Both circuits produce the same truth table."
        )

    return (
        f"The actual expression `{actual_expression}` does not match "
        f"the expected expression `{expected_expression}`. "
        f"There are {len(mismatches)} mismatched truth-table rows. "
        "Check the gate type, inverted inputs, and connections. "
        f"The expected expression is `{expected_expression}`."
    )


# --------------------------------------------------
# 2. VERILOG UTILITIES
# --------------------------------------------------

def clean_verilog(code):
    code = re.sub(r"//.*", "", code)
    code = re.sub(
        r"/\*.*?\*/",
        "",
        code,
        flags=re.DOTALL
    )
    return code


def normalize_verilog_expression(expression):
    expression = re.sub(
        r"1\s*'\s*b\s*0",
        "0",
        expression,
        flags=re.IGNORECASE
    )

    expression = re.sub(
        r"1\s*'\s*b\s*1",
        "1",
        expression,
        flags=re.IGNORECASE
    )

    expression = expression.replace("&&", "&")
    expression = expression.replace("||", "|")
    expression = expression.replace("!", "~")

    return expression.strip()


def get_gate_type(operator):
    if isinstance(operator, ast.BitAnd):
        return "AND"

    if isinstance(operator, ast.BitOr):
        return "OR"

    if isinstance(operator, ast.BitXor):
        return "XOR"

    if isinstance(operator, ast.Invert):
        return "NOT"

    return "UNKNOWN"


# --------------------------------------------------
# 3. EXTRACT GATES FROM BOOLEAN EXPRESSIONS
# --------------------------------------------------

def extract_expression_gates(expression, output_signal, source):
    expression = normalize_verilog_expression(expression)

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError(
            f"Unsupported expression: {expression}"
        ) from exc

    gates = []
    counter = [0]

    def extract(node, is_root=False):

        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.Constant):
            return str(int(bool(node.value)))

        if isinstance(node, ast.UnaryOp):
            input_signal = extract(node.operand)

            if not isinstance(node.op, ast.Invert):
                raise ValueError("Unsupported unary operation.")

            counter[0] += 1

            gate_output = (
                output_signal
                if is_root
                else f"__{output_signal}_G{counter[0]}"
            )

            gates.append({
                "gate_id": f"{output_signal}_G{counter[0]}",
                "gate_type": "NOT",
                "inputs": [input_signal],
                "output": gate_output,
                "source": source
            })

            return gate_output

        if isinstance(node, ast.BinOp):
            left = extract(node.left)
            right = extract(node.right)

            gate_type = get_gate_type(node.op)

            if gate_type == "UNKNOWN":
                raise ValueError("Unsupported gate operation.")

            counter[0] += 1

            gate_output = (
                output_signal
                if is_root
                else f"__{output_signal}_G{counter[0]}"
            )

            gates.append({
                "gate_id": f"{output_signal}_G{counter[0]}",
                "gate_type": gate_type,
                "inputs": [left, right],
                "output": gate_output,
                "source": source
            })

            return gate_output

        raise ValueError("Unsupported expression element.")

    extract(tree.body, is_root=True)

    return gates


# --------------------------------------------------
# 4. VERILOG STRUCTURAL ANALYSIS
# --------------------------------------------------

def analyze_verilog_code(verilog_code):

    if not verilog_code.strip():
        raise ValueError("Please paste Verilog code.")

    code = clean_verilog(verilog_code)

    module_match = re.search(
        r"\bmodule\s+(\w+)\s*(?:\((.*?)\))?\s*;",
        code,
        re.DOTALL
    )

    if not module_match or "endmodule" not in code:
        raise ValueError(
            "A valid module and endmodule are required."
        )

    module_name = module_match.group(1)
    header = module_match.group(2) or ""
    body = code[module_match.end():]

    inputs = []
    outputs = []
    wires = []

    def add_signal(target, name):
        if name not in target:
            target.append(name)

    # Read ANSI-style module declarations.
    for segment in header.split(","):
        match = re.match(
            r"\s*(input|output)\s+(.*)",
            segment
        )

        if match:
            kind = match.group(1)

            name = re.sub(
                r"\b(wire|reg|logic|signed)\b",
                "",
                match.group(2)
            ).strip()

            if not re.fullmatch(r"[A-Za-z_]\w*", name):
                raise ValueError(
                    "Unsupported module port declaration."
                )

            add_signal(
                inputs if kind == "input" else outputs,
                name
            )

    # Read module-body declarations.
    declaration_pattern = (
        r"\b(input|output|wire|reg|logic)\b([^;]*);"
    )

    for kind, declaration in re.findall(
        declaration_pattern,
        body
    ):
        if "[" in declaration or "]" in declaration:
            raise ValueError(
                "Vector signals are not supported."
            )

        declaration = re.sub(
            r"\b(wire|reg|logic|signed)\b",
            "",
            declaration
        )

        for part in declaration.split(","):
            name = part.strip()

            if not re.fullmatch(r"[A-Za-z_]\w*", name):
                raise ValueError(
                    f"Unsupported signal declaration: {name}"
                )

            if kind == "input":
                add_signal(inputs, name)

            elif kind == "output":
                add_signal(outputs, name)

            else:
                add_signal(wires, name)

    if not inputs:
        raise ValueError("No input signals were found.")

    if not outputs:
        raise ValueError("No output signals were found.")

    assignments = {}
    structural_gates = []

    # Continuous assignments.
    assign_matches = re.findall(
        r"\bassign\s+(\w+)\s*=\s*(.*?);",
        body,
        re.DOTALL
    )

    for signal, expression in assign_matches:

        if signal in assignments:
            raise ValueError(
                f"Multiple drivers found for signal {signal}."
            )

        expression = normalize_verilog_expression(expression)

        assignments[signal] = expression

        structural_gates.extend(
            extract_expression_gates(
                expression,
                signal,
                "continuous assign"
            )
        )

    # Gate primitives.
    gate_pattern = (
        r"\b(and|or|not|nand|nor|xor|xnor)"
        r"\s+(?:\w+\s*)?\(([^;]+)\);"
    )

    gate_matches = re.findall(
        gate_pattern,
        body,
        re.IGNORECASE
    )

    for gate, arguments in gate_matches:
        gate = gate.lower()

        signals = [
            item.strip()
            for item in arguments.split(",")
        ]

        if len(signals) < 2:
            raise ValueError(
                f"Invalid {gate.upper()} gate connection."
            )

        output_signal = signals[0]
        gate_inputs = signals[1:]

        if gate == "not" and len(gate_inputs) != 1:
            raise ValueError("NOT gate requires one input.")

        if gate != "not" and len(gate_inputs) < 2:
            raise ValueError(
                f"{gate.upper()} gate requires at least two inputs."
            )

        if output_signal in assignments:
            raise ValueError(
                f"Multiple drivers found for signal {output_signal}."
            )

        if gate == "and":
            expression = " & ".join(gate_inputs)
        elif gate == "or":
            expression = " | ".join(gate_inputs)
        elif gate == "not":
            expression = "~(" + gate_inputs[0] + ")"
        elif gate == "nand":
            expression = "~(" + " & ".join(gate_inputs) + ")"
        elif gate == "nor":
            expression = "~(" + " | ".join(gate_inputs) + ")"
        elif gate == "xor":
            expression = " ^ ".join(gate_inputs)
        else:
            expression = "~(" + " ^ ".join(gate_inputs) + ")"

        assignments[output_signal] = expression

        structural_gates.append({
            "gate_id": f"{output_signal}_PRIMITIVE",
            "gate_type": gate.upper(),
            "inputs": gate_inputs,
            "output": output_signal,
            "source": "gate primitive"
        })

    if not assignments:
        raise ValueError(
            "No supported assign statements or gate primitives found."
        )

    # Resolve intermediate wire connections.
    def resolve_signal(signal, visited=None):

        if visited is None:
            visited = set()

        if signal in inputs:
            return signal

        if signal not in assignments:
            raise ValueError(
                f"Signal '{signal}' has no input or logic definition."
            )

        if signal in visited:
            raise ValueError(
                "Circular connection detected."
            )

        visited = visited | {signal}
        expression = assignments[signal]

        tokens = set(
            re.findall(r"\b[A-Za-z_]\w*\b", expression)
        )

        for token in sorted(tokens, key=len, reverse=True):
            if token in assignments:

                replacement = resolve_signal(
                    token,
                    visited
                )

                expression = re.sub(
                    rf"\b{re.escape(token)}\b",
                    f"({replacement})",
                    expression
                )

        return expression

    resolved_expressions = {}

    for output in outputs:
        resolved_expressions[output] = resolve_signal(output)

    # Generate truth tables.
    truth_tables = {}

    for output, expression in resolved_expressions.items():
        truth_tables[output] = generate_truth_table(
            expression,
            inputs
        )

    # Validate structural connections, including generated internal nodes.
    known_signals = set(inputs) | set(outputs) | set(wires)
    known_signals.update(assignments.keys())

    for gate in structural_gates:
        known_signals.add(gate["output"])

    for gate in structural_gates:
        for signal in gate["inputs"]:
            if signal not in known_signals and signal not in ("0", "1"):
                raise ValueError(
                    f"Gate {gate['gate_id']} uses undefined signal "
                    f"'{signal}'."
                )

    return {
        "module_name": module_name,
        "inputs": inputs,
        "outputs": outputs,
        "wires": wires,
        "assignments": assignments,
        "expressions": resolved_expressions,
        "truth_tables": truth_tables,
        "gates": structural_gates,
        "gate_count": len(structural_gates)
    }


# --------------------------------------------------
# 5. GATE NETWORK EVALUATION
# --------------------------------------------------

def apply_gate(gate_type, values):

    gate_type = gate_type.upper()
    values = [bool(value) for value in values]

    if gate_type == "AND":
        return int(all(values))

    if gate_type == "OR":
        return int(any(values))

    if gate_type == "NOT":
        if len(values) != 1:
            raise ValueError("NOT requires one input.")
        return int(not values[0])

    if gate_type == "NAND":
        return int(not all(values))

    if gate_type == "NOR":
        return int(not any(values))

    if gate_type == "XOR":
        return int(sum(values) % 2 == 1)

    if gate_type == "XNOR":
        return int(sum(values) % 2 == 0)

    raise ValueError(f"Unknown gate type: {gate_type}")


def evaluate_gate_network(
    gates,
    input_values,
    output_signal
):
    """
    Evaluate a structural gate network.
    Gates are evaluated when all their input signals are available.
    """

    signals = dict(input_values)

    remaining = list(gates)

    while remaining:
        progress = False

        for gate in remaining[:]:

            if all(
                signal in signals
                for signal in gate["inputs"]
            ):
                gate_inputs = [
                    signals[signal]
                    for signal in gate["inputs"]
                ]

                signals[gate["output"]] = apply_gate(
                    gate["gate_type"],
                    gate_inputs
                )

                remaining.remove(gate)
                progress = True

        if not progress:
            unresolved = [
                gate["gate_id"]
                for gate in remaining
            ]

            raise ValueError(
                "Unable to evaluate gate connections. "
                f"Unresolved gates: {unresolved}"
            )

    if output_signal not in signals:
        raise ValueError(
            f"Output signal {output_signal} was not generated."
        )

    return signals[output_signal]


# --------------------------------------------------
# 6. STRUCTURAL FAULT DIAGNOSIS
# --------------------------------------------------

def get_circuit_structure(verilog_code):

    analysis = analyze_verilog_code(verilog_code)

    return {
        "module_name": analysis["module_name"],
        "inputs": analysis["inputs"],
        "outputs": analysis["outputs"],
        "wires": analysis["wires"],
        "gate_count": analysis["gate_count"],
        "gates": analysis["gates"],
        "expressions": analysis["expressions"]
    }


def compare_expected_with_verilog(
    verilog_code,
    expected_expression,
    output_signal
):
    analysis = analyze_verilog_code(verilog_code)

    if output_signal not in analysis["outputs"]:
        raise ValueError(
            f"Output '{output_signal}' was not found."
        )

    expected_rows = generate_truth_table(
        expected_expression,
        analysis["inputs"]
    )

    actual_rows = analysis["truth_tables"][output_signal]

    mismatches = compare_truth_tables(
        expected_rows,
        actual_rows,
        analysis["inputs"]
    )

    return {
        "analysis": analysis,
        "expected_rows": expected_rows,
        "actual_rows": actual_rows,
        "mismatches": mismatches,
        "passed": len(mismatches) == 0,
        "structure": get_circuit_structure(verilog_code)
    }


def diagnose_gate_faults(
    verilog_code,
    expected_expression,
    output_signal,
    max_faults=2,
    max_candidates=10000
):
    """
    Search for gate-type replacements that make the circuit
    match the expected truth table.

    Preserves all existing gate connections.
    Searches one-gate and multiple-gate type changes.
    """

    if max_faults < 1:
        raise ValueError("max_faults must be at least 1.")

    if max_candidates < 1:
        raise ValueError("max_candidates must be at least 1.")

    analysis = analyze_verilog_code(verilog_code)

    if output_signal not in analysis["outputs"]:
        raise ValueError(
            f"Output '{output_signal}' was not found."
        )

    inputs = analysis["inputs"]
    original_gates = analysis["gates"]

    if not original_gates:
        raise ValueError("No structural gates were found.")

    expected_rows = generate_truth_table(
        expected_expression,
        inputs
    )

    expected_outputs = [
        row["Output"]
        for row in expected_rows
    ]

    def network_matches(gates):
        actual_outputs = []

        for row in expected_rows:
            input_values = {
                name: row[name]
                for name in inputs
            }

            result = evaluate_gate_network(
                gates,
                input_values,
                output_signal
            )

            actual_outputs.append(result)

        return actual_outputs == expected_outputs

    original_outputs = []

    for row in expected_rows:
        input_values = {
            name: row[name]
            for name in inputs
        }

        original_outputs.append(
            evaluate_gate_network(
                original_gates,
                input_values,
                output_signal
            )
        )

    if original_outputs == expected_outputs:
        return {
            "status": "NO_FAULT",
            "message": "The circuit already matches expected behaviour.",
            "original_gate_count": len(original_gates),
            "faults_found": 0,
            "candidates": [],
            "search_complete": True,
            "candidates_tested": 0
        }

    candidates = []
    candidates_tested = 0
    search_complete = True

    # Search smaller repairs first.
    maximum_faults = min(
        max_faults,
        len(original_gates)
    )

    for number_of_faults in range(1, maximum_faults + 1):

        found_at_this_level = False

        for selected_indices in combinations(
            range(len(original_gates)),
            number_of_faults
        ):

            replacement_options = []

            for index in selected_indices:
                gate = original_gates[index]

                if len(gate["inputs"]) == 1:
                    possible_types = ["NOT"]
                else:
                    possible_types = [
                        "AND", "OR", "NAND",
                        "NOR", "XOR", "XNOR"
                    ]

                possible_types = [
                    gate_type
                    for gate_type in possible_types
                    if gate_type != gate["gate_type"]
                ]

                replacement_options.append(possible_types)

            for replacements in product(*replacement_options):

                if candidates_tested >= max_candidates:
                    search_complete = False
                    break

                candidates_tested += 1

                modified_gates = [
                    dict(gate)
                    for gate in original_gates
                ]

                repair_details = []

                for index, new_type in zip(
                    selected_indices,
                    replacements
                ):
                    old_gate = modified_gates[index]
                    old_type = old_gate["gate_type"]

                    old_gate["gate_type"] = new_type

                    repair_details.append({
                        "gate_id": old_gate["gate_id"],
                        "output": old_gate["output"],
                        "inputs": old_gate["inputs"],
                        "original_type": old_type,
                        "suggested_type": new_type,
                        "repair": (
                            f"Replace {old_type} with {new_type} "
                            f"at gate {old_gate['gate_id']}."
                        )
                    })

                if network_matches(modified_gates):
                    found_at_this_level = True

                    candidates.append({
                        "fault_count": number_of_faults,
                        "repairs": repair_details,
                        "corrected_gates": modified_gates,
                        "verified": True
                    })

            if not search_complete:
                break

        # Return the simplest successful repairs.
        if found_at_this_level:
            break

        if not search_complete:
            break

    if candidates:
        return {
            "status": "REPAIR_FOUND",
            "message": (
                "One or more gate-type replacement combinations "
                "match the expected truth table."
            ),
            "original_gate_count": len(original_gates),
            "faults_found": candidates[0]["fault_count"],
            "candidates": candidates,
            "search_complete": search_complete,
            "candidates_tested": candidates_tested
        }

    return {
        "status": "NO_REPAIR_FOUND",
        "message": (
            "No matching gate-type replacement was found "
            "within the configured search limits. "
            "A connection fault or unsupported circuit may be present."
        ),
        "original_gate_count": len(original_gates),
        "faults_found": None,
        "candidates": [],
        "search_complete": search_complete,
        "candidates_tested": candidates_tested
    }


# --------------------------------------------------
# 7. CORRECTED VERILOG GENERATION
# --------------------------------------------------

def generate_corrected_verilog(
    expected_expression,
    input_signals,
    output_signal,
    module_name="corrected_logic"
):

    if not re.fullmatch(r"[A-Za-z_]\w*", module_name):
        raise ValueError("Invalid Verilog module name.")

    if not re.fullmatch(r"[A-Za-z_]\w*", output_signal):
        raise ValueError("Invalid Verilog output signal name.")

    if not input_signals:
        raise ValueError("At least one input signal is required.")

    if output_signal in input_signals:
        raise ValueError(
            "Output signal cannot also be an input."
        )

    for signal in input_signals:
        if not re.fullmatch(r"[A-Za-z_]\w*", signal):
            raise ValueError(
                f"Invalid Verilog input signal: {signal}"
            )

    if len(input_signals) != len(set(input_signals)):
        raise ValueError(
            "Duplicate input signals are not allowed."
        )

    generate_truth_table(
        expected_expression,
        input_signals
    )

    input_list = ", ".join(input_signals)

    return f"""module {module_name}({input_list}, {output_signal});

input {input_list};
output {output_signal};

assign {output_signal} = {expected_expression};

endmodule
"""


# --------------------------------------------------
# 8. CORRECTED VERILOG VERIFICATION
# --------------------------------------------------

def verify_corrected_verilog(
    corrected_code,
    expected_expression,
    output_signal
):

    analysis = analyze_verilog_code(corrected_code)

    if output_signal not in analysis["outputs"]:
        raise ValueError(
            f"Output '{output_signal}' was not found in corrected code."
        )

    inputs = analysis["inputs"]

    expected_rows = generate_truth_table(
        expected_expression,
        inputs
    )

    actual_rows = analysis["truth_tables"][output_signal]

    mismatches = compare_truth_tables(
        expected_rows,
        actual_rows,
        inputs
    )

    return {
        "analysis": analysis,
        "expected_rows": expected_rows,
        "actual_rows": actual_rows,
        "mismatches": mismatches,
        "passed": len(mismatches) == 0
    }
