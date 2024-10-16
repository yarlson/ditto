import os
import json
import traceback
from flask import (
    Flask,
    request,
    render_template_string,
    jsonify,
)
from threading import Thread
from time import sleep

# Correctly import the completion function from LiteLLM
from litellm import completion, supports_function_calling

# Configuration
MODEL_NAME = os.environ.get(
    "LITELLM_MODEL", "gpt-4o"
)  # Default model; can be swapped easily

# Initialize Flask app
app = Flask(__name__)

LOG_FILE = "go_cli_builder_log.json"

# Directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(BASE_DIR, "go_cli_project")  # New project directory
CMD_DIR = os.path.join(PROJECT_DIR, "cmd")
PKG_DIR = os.path.join(PROJECT_DIR, "pkg")

# Initialize progress tracking
progress = {
    "status": "idle",
    "iteration": 0,
    "max_iterations": 50,
    "output": "",
    "completed": False,
}


# Ensure directories exist
def create_directory(path):
    # Ensure that the path is within the PROJECT_DIR
    full_path = os.path.join(PROJECT_DIR, path)
    if not os.path.exists(full_path):
        os.makedirs(full_path)
        return f"Created directory: {full_path}"
    return f"Directory already exists: {full_path}"


def create_file(path, content):
    # Ensure that the path is within the PROJECT_DIR
    full_path = os.path.join(PROJECT_DIR, path)
    directory = os.path.dirname(full_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    try:
        with open(full_path, "x") as f:
            f.write(content)
        return f"Created file: {full_path}"
    except FileExistsError:
        with open(full_path, "w") as f:
            f.write(content)
        return f"Updated file: {full_path}"
    except Exception as e:
        return f"Error creating/updating file {full_path}: {e}"


def update_file(path, content):
    # Ensure that the path is within the PROJECT_DIR
    full_path = os.path.join(PROJECT_DIR, path)
    try:
        with open(full_path, "w") as f:
            f.write(content)
        return f"Updated file: {full_path}"
    except Exception as e:
        return f"Error updating file {full_path}: {e}"


def fetch_code(file_path):
    # Ensure that the path is within the PROJECT_DIR
    full_path = os.path.join(PROJECT_DIR, file_path)
    try:
        with open(full_path, "r") as f:
            code = f.read()
        return code
    except Exception as e:
        return f"Error fetching code from {full_path}: {e}"


def task_completed():
    progress["status"] = "completed"
    progress["completed"] = True
    return "Task marked as completed."


# Initialize necessary directories
create_directory("cmd")
create_directory("pkg")


# Function to log history to file
def log_to_file(history_dict):
    try:
        with open(LOG_FILE, "w") as log_file:
            json.dump(history_dict, log_file, indent=4)
    except Exception as e:
        print(
            f"Error logging to file: {e}"
        )  # Log the error instead of silently failing


# Default route to render a form
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        user_input = request.form.get("user_input")
        # Run the main loop with the user's input in a separate thread
        progress["status"] = "running"
        progress["iteration"] = 0
        progress["output"] = ""
        progress["completed"] = False
        thread = Thread(target=run_main_loop, args=(user_input,))
        thread.start()
        return render_template_string(
            """
            <h1>Progress</h1>
            <pre id="progress">{{ progress_output }}</pre>
            <script>
                setInterval(function() {
                    fetch('/progress')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('progress').innerHTML = data.output;
                        if (data.completed) {
                            document.getElementById('refresh-btn').style.display = 'block';
                        }
                    });
                }, 2000);
            </script>
            <button id="refresh-btn" style="display:none;" onclick="location.reload();">Refresh Page</button>
        """,
            progress_output=progress["output"],
        )
    else:
        return render_template_string(
            """
            <h1>Go CLI Builder</h1>
            <form method="post">
                <label for="user_input">Describe the Go CLI application you want to create:</label><br>
                <input type="text" id="user_input" name="user_input"><br><br>
                <input type="submit" value="Submit">
            </form>
        """
        )


# Route to provide progress updates
@app.route("/progress")
def get_progress():
    return jsonify(progress)


# Available functions for the LLM
available_functions = {
    "create_directory": create_directory,
    "create_file": create_file,
    "update_file": update_file,
    "fetch_code": fetch_code,
    "task_completed": task_completed,
}

# Define the tools for function calling
tools = [
    {
        "type": "function",
        "function": {
            "name": "create_directory",
            "description": "Creates a new directory at the specified path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The directory path to create.",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Creates or updates a file at the specified path with the given content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path to create or update.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write into the file.",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_file",
            "description": "Updates an existing file at the specified path with the new content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path to update.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The new content to write into the file.",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_code",
            "description": "Retrieves the code from the specified file path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The file path to fetch the code from.",
                    }
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "task_completed",
            "description": "Indicates that the assistant has completed the task.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


def run_main_loop(user_input):
    # Reset the history_dict for each run
    history_dict = {"iterations": []}

    if not supports_function_calling(MODEL_NAME):
        progress["status"] = "error"
        progress["output"] = "Model does not support function calling."
        progress["completed"] = True
        return "Model does not support function calling."

    max_iterations = progress["max_iterations"]  # Prevent infinite loops
    iteration = 0

    # Updated messages array with enhanced prompt
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert Go developer experienced in building command-line applications using the Cobra framework. "
                "You are tasked with building a complete, production-ready Go CLI application based on the user's description. "
                "Before coding, carefully plan out all the commands, subcommands, flags, and necessary packages. "
                "Follow these steps:\n"
                "1. **Understand the Requirements**: Analyze the user's input to fully understand the application's functionality and features.\n"
                "2. **Plan the Application Structure**: List all the commands, subcommands, flags, and packages that need to be created. Consider how they interact.\n"
                "3. **Implement Step by Step**: For each component, use the provided tools to create directories, files, and write code. Ensure each step is thoroughly completed before moving on.\n"
                "4. **Review and Refine**: Use `fetch_code` to review the code you've written. Update files if necessary using `update_file`.\n"
                "5. **Ensure Completeness**: Do not leave any placeholders or incomplete code. All commands, subcommands, and functionalities must be fully implemented and ready for production.\n"
                "6. **Create Entry Point `main.go`**: Make sure to create an entry point `main.go` file in the project directory.\n"
                "7. **Do Not Modify `main.py`**: Focus only on creating Go source files within the appropriate directories.\n"
                "8. **Finalize**: Once everything is complete and thoroughly tested, call `task_completed()` to finish.\n\n"
                "Constraints and Notes:\n"
                "- The application files must be structured within a project subfolder, following Go conventions, such as `cmd/` and `pkg/`.\n"
                "- All file paths are relative to the project directory.\n"
                "- Commands should be modular and placed inside the `cmd/` directory.\n"
                "- Do not use placeholders like 'TODO'. All code should be complete and functional.\n"
                "- Do not ask the user for additional input; infer any necessary details to complete the application.\n"
                "- Ensure all commands and subcommands are properly linked and that flags and options are correctly implemented.\n"
                "- Handle any errors internally and attempt to resolve them before proceeding.\n\n"
                "Available Tools:\n"
                "- `create_directory(path)`: Create a new directory relative to the project directory.\n"
                "- `create_file(path, content)`: Create or overwrite a file with content relative to the project directory.\n"
                "- `update_file(path, content)`: Update an existing file with new content relative to the project directory.\n"
                "- `fetch_code(file_path)`: Retrieve the code from a file for review relative to the project directory.\n"
                "- `task_completed()`: Call this when the application is fully built and ready.\n\n"
                "Remember to think carefully at each step, ensuring the application is complete, functional, and meets the user's requirements."
            ),
        },
        {"role": "user", "content": user_input},
        {
            "role": "system",
            "content": f"History:\n{json.dumps(history_dict, indent=2)}",
        },
    ]

    output = ""

    while iteration < max_iterations:
        progress["iteration"] = iteration + 1
        # Create a new iteration dictionary for each loop
        current_iteration = {
            "iteration": iteration + 1,  # Start from 1
            "actions": [],
            "llm_responses": [],
            "tool_results": [],
            "errors": [],
        }
        history_dict["iterations"].append(current_iteration)

        try:
            response = completion(
                model=MODEL_NAME, messages=messages, tools=tools, tool_choice="auto"
            )

            if not response.choices[0].message:
                error = response.get("error", "Unknown error")
                current_iteration["errors"].append(
                    {"action": "llm_completion", "error": error}
                )
                log_to_file(history_dict)
                sleep(5)
                iteration += 1
                continue

            # Extract LLM response and append to current iteration
            response_message = response.choices[0].message
            content = response_message.content or ""
            current_iteration["llm_responses"].append(content)

            # Prepare the output string
            output += f"\n<h2>Iteration {iteration + 1}:</h2>\n"

            tool_calls = response_message.tool_calls

            if tool_calls:
                output += "<strong>Tool Call:</strong>\n<p>" + content + "</p>\n"
                messages.append(response_message)

                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_to_call = available_functions.get(function_name)

                    if not function_to_call:
                        error_message = f"Tool '{function_name}' is not available."
                        current_iteration["errors"].append(
                            {
                                "action": f"tool_call_{function_name}",
                                "error": error_message,
                                "traceback": "No traceback available.",
                            }
                        )
                        continue

                    try:
                        function_args = json.loads(tool_call.function.arguments)

                        # Call the tool function and store result
                        function_response = function_to_call(**function_args)

                        # Append the tool result under the current iteration
                        current_iteration["tool_results"].append(
                            {"tool": function_name, "result": function_response}
                        )

                        # Include tool result in the output
                        output += f"<strong>Tool Result ({function_name}):</strong>\n<p>{function_response}</p>\n"

                        # Add tool call details to the conversation
                        messages.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": function_response,
                            }
                        )

                        # Check if the assistant called 'task_completed' to signal completion
                        if function_name == "task_completed":
                            progress["status"] = "completed"
                            progress["completed"] = True
                            output += "\n<h2>COMPLETE</h2>\n"
                            progress["output"] = output
                            log_to_file(history_dict)
                            return output  # Exit the function

                    except Exception as tool_error:
                        error_message = f"Error executing {function_name}: {tool_error}"
                        current_iteration["errors"].append(
                            {
                                "action": f"tool_call_{function_name}",
                                "error": error_message,
                                "traceback": traceback.format_exc(),
                            }
                        )

                # Second response to include the tool call
                second_response = completion(model=MODEL_NAME, messages=messages)
                if second_response.choices and second_response.choices[0].message:
                    second_response_message = second_response.choices[0].message
                    content = second_response_message.content or ""
                    current_iteration["llm_responses"].append(content)
                    output += "<strong>LLM Response:</strong>\n<p>" + content + "</p>\n"
                    messages.append(second_response_message)
                else:
                    error = second_response.get(
                        "error", "Unknown error in second LLM response."
                    )
                    current_iteration["errors"].append(
                        {"action": "second_llm_completion", "error": error}
                    )

            else:
                output += "<strong>LLM Response:</strong>\n<p>" + content + "</p>\n"
                messages.append(response_message)

            progress["output"] = output

        except Exception as e:
            error = str(e)
            current_iteration["errors"].append(
                {
                    "action": "main_loop",
                    "error": error,
                    "traceback": traceback.format_exc(),
                }
            )

        iteration += 1
        log_to_file(history_dict)
        sleep(2)

    if iteration >= max_iterations:
        progress["status"] = "completed"

    progress["completed"] = True
    progress["status"] = "completed"

    return output


if __name__ == "__main__":
    # Start the Flask app
    app.run(host="0.0.0.0", port=8080)
