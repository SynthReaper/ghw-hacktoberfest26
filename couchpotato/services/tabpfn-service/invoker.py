"""
CLI Invoker for TabPFN MCP Service
Safely reads arguments from stdin and outputs __RESULT_START__ JSON __RESULT_END__
"""

import sys
import json
import os

# Add server directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import classify_expense, detect_bill_spike, audit_schedule_c

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing tool name argument"}))
        sys.exit(1)

    tool_name = sys.argv[1]
    input_text = sys.stdin.read()
    args = json.loads(input_text) if input_text.strip() else {}

    if tool_name == "classify_expense":
        res = classify_expense(**args)
    elif tool_name == "detect_bill_spike":
        res = detect_bill_spike(**args)
    elif tool_name == "audit_schedule_c":
        res = audit_schedule_c(**args)
    else:
        res = {"error": f"Unknown tool {tool_name}"}

    print("__RESULT_START__" + json.dumps(res) + "__RESULT_END__")

if __name__ == "__main__":
    main()
