# Ditto

[![License](https://img.shields.io/github/license/yarlson/ditto)](LICENSE)

**Ditto** - _the simplest self-building coding agent_.

Ditto is a user-friendly tool that allows you to generate a multi-file Go command-line application using Go and Cobra from simple natural language descriptions. By leveraging a simple LLM loop with a few tools, Ditto automates the coding process, (occasionally) turning your ideas into functional command-line applications (or at least trying and getting close).

## Features

- **Simple Natural Language Input**: Just describe the command-line application you want to build in plain English.
- **Automated Code Generation**: Generates commands, subcommands, and necessary Go source files based on your description.
- **Self-Building Agent**: Automatically plans and constructs the application without the need for manual coding.
- **Modular Structure**: Organizes code into a clean, modular structure with separate directories for commands and packages.
- **Isolated Project Directory**: All generated files are contained within a `go_cli_project` subfolder to keep your workspace organized.
- **Entrypoint Creation**: Automatically creates an entrypoint `main.go` file for your Go application.

## Getting Started

### Prerequisites

- Python 3.7 or higher
- `pip` package manager
- Go 1.16 or higher

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yarlson/ditto.git
   cd ditto
   ```

2. **Create a Virtual Environment (Optional but Recommended)**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install litellm
   ```

### Setting the `OPENAI_API_KEY`

To use Ditto, you'll need to set the `OPENAI_API_KEY` in your environment. Here are two options for doing that:

#### Option 1: Temporary Setup in Terminal

For macOS/Linux:

```bash
export OPENAI_API_KEY=your-openai-api-key
```

For Windows (Command Prompt):

```cmd
set OPENAI_API_KEY=your-openai-api-key
```

For Windows (PowerShell):

```powershell
$env:OPENAI_API_KEY="your-openai-api-key"
```

Run the application:

```bash
python main.py
```

#### Option 2: Persistent Setup using a `.env` File (Recommended)

1. Install the `python-dotenv` package to load environment variables from a `.env` file:

   ```bash
   pip install python-dotenv
   ```

2. Create a `.env` file in the root of the project directory and add your API key:

   ```bash
   OPENAI_API_KEY=your-openai-api-key
   ```

3. Run the application as usual:

   ```bash
   python main.py
   ```

### Usage

1. **Run the Application**

   ```bash
   python main.py
   ```

2. **Access the Web Interface**

   Open your web browser and navigate to `http://localhost:8080`.

3. **Describe Your Application**

   On the home page, you'll find a form where you can describe the Go CLI application you want to create.

4. **Monitor Progress**

   After submitting your description, the application will process your request. You can monitor the progress in real-time.

5. **View the Generated Application**

   Once the process is complete, your Go CLI application will be generated inside the `go_cli_project` directory, keeping your workspace organized.

6. **Compile and Run Your Application**

   Navigate to the `go_cli_project` directory:

   ```bash
   cd go_cli_project
   ```

   Build the application:

   ```bash
   go build -o myapp
   ```

   Replace `myapp` with the desired name for your executable.

   Run the application:

   ```bash
   ./myapp
   ```

   Or, if you prefer to run it directly without building:

   ```bash
   go run main.go
   ```

## Contribution

This is a quick exploration, so I have no plans to work on this further. Contributions are welcome, especially if they are awesome, but ping me on X/Twitter because I don't check PRs often. I'm basically going to try to bake this into the new [BabyAGI framework](https://github.com/yarlson/babyagi), but give it the ability to store and save functions from the database. If this sounds like a fun challenge and you get it working, definitely let me know :)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
