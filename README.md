# LOGICOM - Rewritten Architecture

This directory contains a refactored version of the LOGICOM project, designed for improved modularity, maintainability, and extensibility, particularly regarding the use of different Large Language Models (LLMs).

## Architecture Overview

This project simulates and analyzes debates between AI agents on specific topics/claims using a structured, modular architecture.

**Core Architecture Principles:**

1.  **Orchestration Pattern:** The system is centered around a `DebateOrchestrator` (`core/orchestrator.py`), which manages the turn-by-turn flow of the debate, including agent interactions and moderation checks.
2.  **Agent-Based System:** The debate involves distinct AI agents, each with specific roles:
    *   `PersuaderAgent`: Aims to convince the `DebaterAgent` of the claim. It can optionally use a "helper" LLM to refine its arguments or identify fallacies in the opponent's reasoning.
    *   `DebaterAgent`: Responds to the `PersuaderAgent`, typically arguing against the claim or seeking clarification.
    *   `ModeratorAgent`: Multiple instances monitor the debate based on specific criteria (termination conditions, topic relevance, signal detection like `[CONVINCED]`) using dedicated prompts.
3.  **Modular Components & Interfaces:** Key functionalities are separated into modules with clearly defined interfaces (`core/interfaces.py`):
    *   `AgentInterface`: Abstract base for all agent types.
    *   `LLMInterface`: Abstract base for interacting with different Large Language Models.
    *   `MemoryInterface`: Abstract base for managing conversation history for each agent (e.g., `ChatSummaryMemory` handles context limits via summarization or truncation).
4.  **Configuration Driven:** System behavior is heavily controlled by YAML configuration files (`config/settings.yaml`, `config/models.yaml`). This allows easy modification of:
    *   Debate parameters (max rounds, delays).
    *   Agent configurations (LLM choice, prompts, helper usage).
    *   LLM provider details (model names, API keys/endpoints).
    *   Data paths and logging settings.
5.  **LLM Abstraction:** An `LLMFactory` (`llm/llm_factory.py`) creates specific LLM client instances (e.g., `OpenAIClient`, `GeminiClient`, `LocalClient`) based on the configuration, abstracting the underlying API details.
6.  **Prompt Management:** Agent prompts (system instructions, wrappers, helper prompts) are loaded from external files (typically in `prompts/`) and dynamically formatted with claim-specific data.
7.  **Data Handling:** Debates are initiated based on claims loaded from a dataset (e.g., CSV), specified in the configuration.
8.  **Entry Point & Setup (`main.py`):** The main script handles command-line arguments, loads configurations (`config/loader.py`), sets up API keys (`utils/set_api_keys.py`), prepares the debate environment *for each claim* by instantiating `core.debate_setup.DebateInstanceSetup` (which creates agents, LLMs, memory), iterates through claims, and invokes the orchestrator.
9.  **Logging & Output:** Detailed debate logs (transcripts, results, metadata, token usage) are saved to structured directories. Logs are saved per claim and configuration in the format `debates/<topic_id>/<helper_type>/<chat_id>/`. Each debate directory contains JSONL log files (`debate_main.log`, `debate_debug.log`, etc.) and a summary Excel file (`all_debates_summary.xlsx`) is saved in the project root. Logging is handled by Python's logging framework configured in `utils/log_main.py`.

**Overall Flow:**

`main.py` -> Load Config -> Load Data -> For each Claim -> Instantiate `DebateInstanceSetup` (Create LLMs, Memory, Agents based on config) -> Instantiate `DebateOrchestrator` -> `Orchestrator.run_debate()` -> [Debate Loop: Persuader Turn -> Debater Turn -> Moderator Checks -> Evaluate Termination Conditions] -> Save Results to Excel -> Summarize Run.

This architecture promotes modularity and configurability, making it easier to experiment with different LLMs, prompts, agent strategies, and debate parameters.

## Directory Structure

```
LOGICOM/ # Project Root
├── main.py                 # Main entry point: parses args, loads config, sets up, runs debates
├── core/
│   ├── interfaces.py       # Defines core ABCs (LLMInterface, AgentInterface, MemoryInterface)
│   ├── orchestrator.py     # High-level debate loop logic, manages agent turns and moderation
│   └── debate_setup.py     # Handles claim-specific setup (prompts, clients, agents, memory)
├── llm/
│   ├── __init__.py
│   ├── llm_factory.py      # Factory to create LLM clients based on config
│   ├── openai_client.py    # Implementation for OpenAI
│   ├── gemini_client.py    # Implementation for Google Gemini
│   └── local_client.py     # Implementations for local LLMs (Ollama, Generic OpenAI-compatible)
├── agents/
│   ├── __init__.py
│   ├── base_agent.py       # Base class for all agents
│   ├── persuader_agent.py  # Persuader agent logic
│   ├── debater_agent.py    # Debater agent logic
│   └── moderator_agent.py  # Moderator agent logic (performs single check)
├── memory/
│   ├── __init__.py
│   └── chat_summary_memory.py # Memory implementation (stores history, formats prompts)
├── prompts/                # Contains prompt template files used by agents
│   └── ...
├── config/
│   ├── __init__.py
│   ├── settings.yaml       # Main config: debate settings, agent setups, LLM references
│   ├── models.yaml         # LLM provider configs: API keys (optional), endpoints, model names
│   └── loader.py           # Logic to load and parse YAML configuration files
├── utils/
│   ├── __init__.py
│   ├── set_api_keys.py     # Script to set API keys as environment variables
│   ├── log_main.py         # Logging configuration and setup
│   ├── utils.py            # Utility functions for directory creation and Excel saving
│   ├── multiple_runs.py     # Script for running multiple debates in parallel
│   ├── analyze_debate_results.py # Analysis script for debate results
│   └── token_utils.py      # Token calculation utilities for LLMs
├── claims/                 # Default data directory containing claim datasets (e.g., CSV)
│   └── ...
├── debates/                # Output directory for debate logs (default location)
│   ├── <topic_id>/         # Subdirectory for each claim/topic
│   │   └── <helper_type>/  # Subdirectory for each agent config run
│   │       └── <chat_id>/  # Individual debate directory
│   │           ├── debate_main.log      # Main debate transcript (JSONL)
│   │           ├── debate_debug.log    # Debug logs (JSONL)
│   │           └── round_data.json     # Round-by-round data
│   └── ...
├── results/                # Output directory for batch runs (created by multiple_runs.py)
│   └── <timestamp>_<run_name>/  # Timestamped results directory
│       ├── debates/        # Debate logs for this batch
│       ├── analysis/       # Analysis results (if analysis script runs)
│       ├── all_debates_summary.xlsx # Summary Excel file
│       ├── settings.yaml   # Copy of settings used
│       └── prompts.zip      # Archive of prompts used
├── all_debates_summary.xlsx # Summary Excel file (created in project root during runs)
├── API_keys                # (Gitignored) File to store API keys locally
├── API_keys.template       # Template for the API keys file
├── requirements.txt        # Python package dependencies
├── .gitignore              # Specifies intentionally untracked files for Git
├── LICENSE                 # Project license information
└── README.md               # This file
```

## Setup

1.  **Install Dependencies:** From within the project root directory:
    ```bash
    pip install -r requirements.txt
    ```
2.  **API Keys:** You need to provide API keys for OpenAI and/or Google Gemini. You can do this in one of the following ways (the application checks in this order):
    *   **Recommended: Use the `set_api_keys.py` script:**
        1. Copy `API_keys.template` to `API_keys` in the project root directory.
        2. Edit `API_keys` with your actual keys, uncommenting the relevant lines.
        3. Run the script *from within the project root directory* to set environment variables for the current session:
           ```bash
           python utils/set_api_keys.py
           ```
    *   **Manual Environment Variables:** Set the variables directly in your terminal session *before* running `main.py`:
        ```bash
        export OPENAI_API_KEY="your_openai_key"
        export GOOGLE_API_KEY="your_google_api_key"
        ```
    *   **(Less Secure) Edit `config/models.yaml`:** Add your keys directly into the `models.yaml` file under the respective provider configurations.

3.  **Data:** Ensure the dataset specified in `config/settings.yaml` (`debate_settings.claims_file_path`) is accessible. The default configuration points to `./claims/all-claim-not-claim.csv` relative to the project root. `main.py` will attempt to resolve this path relative to its own location if the direct path isn't found.
4.  **Prompts:** Ensure the prompt files referenced in `config/settings.yaml` exist within the `prompts/` directory or paths specified.

## Running

### Running Single Debates (`main.py`)

Execute the main script from the project root directory:

```bash
python main.py [OPTIONS]
```

**Options:**

*   `--helper_type <TYPE>`: Specifies which helper type configuration to use (default: `Default_No_Helper`).
*   `--claim_index <INDEX>`: Run only for a specific claim index (0-based) in the dataset. If omitted, runs for all claims.
*   `--settings_path <PATH>`: Path to the settings YAML file (default: `./config/settings.yaml`).
*   `--models_path <PATH>`: Path to the models YAML file (default: `./config/models.yaml`).
*   `--max_rounds <N>`: Override the maximum number of debate rounds from settings.yaml.
*   `--debates_dir <DIR>`: Directory where debate logs should be saved (default: `debates`).

**Examples:**

Run the default 'Default_No_Helper' configuration for claim index 5:
```bash
python main.py --helper_type Default_No_Helper --claim_index 5 
```

Run all claims with a specific helper type:
```bash
python main.py --helper_type Default_Fallacy_Helper
```

Run with custom max rounds:
```bash
python main.py --helper_type Default_No_Helper --max_rounds 5
```

Run with custom debates directory:
```bash
python main.py --helper_type Default_No_Helper --debates_dir my_debates
```

### Running Multiple Debates (`multiple_runs.py`)

For running multiple debates with different configurations in parallel, use the `multiple_runs.py` script:

```bash
python utils/multiple_runs.py [OPTIONS]
```

**Options:**

*   `--run_name <NAME>`: **Required.** Name for this batch run (will be combined with timestamp for results folder).
*   `--helper_types <TYPE1> <TYPE2> ...`: List of helper types to run (default: all available helper types).
*   `--claim_indexes <INDEX1> <INDEX2> ...`: List of specific claim indexes to run (default: all claims).
*   `--settings_path <PATH>`: Path to the settings YAML file (default: `./config/settings.yaml`).
*   `--models_path <PATH>`: Path to the models YAML file (default: `./config/models.yaml`).
*   `--max_workers <N>`: Maximum number of parallel workers (default: 4, use 1 for sequential execution).
*   `--list_helpers`: List all available helper types and exit.

**Features:**

*   **Parallel Execution:** Runs multiple debates concurrently (configurable with `--max_workers`).
*   **Organized Results:** Creates timestamped results directory (`results/<timestamp>_<run_name>/`) containing:
    *   All debate logs in `debates/` subdirectory
    *   Summary Excel file (`all_debates_summary.xlsx`)
    *   Copy of settings used (`settings.yaml`)
    *   Archive of prompts used (`prompts.zip`)
    *   Analysis results (if analysis script runs automatically)
*   **Progress Tracking:** Shows real-time progress with completion status for each run.
*   **Graceful Shutdown:** Supports Ctrl+C for graceful interruption (waits for current debates to finish).

**Examples:**

List available helper types:
```bash
python utils/multiple_runs.py --list_helpers
```

Run all helper types for all claims:
```bash
python utils/multiple_runs.py --run_name my_experiment
```

Run specific helper types for specific claims:
```bash
python utils/multiple_runs.py --run_name test_run --helper_types Default_No_Helper Default_Fallacy_Helper --claim_indexes 0 1 2
```

Run sequentially (single worker):
```bash
python utils/multiple_runs.py --run_name sequential_run --max_workers 1
```

Run with custom settings file:
```bash
python utils/multiple_runs.py --run_name custom_config --settings_path ./config/settings/custom_settings.yaml
```

## Configuration

*   **`config/models.yaml`**: Define different LLM providers (OpenAI, Gemini, local) and their connection details (API keys/endpoints, model names, default parameters).
*   **`config/settings.yaml`**: 
    *   `debate_settings`: Configure data paths (using `claims/` by default), max rounds, turn delays, memory settings (summarization triggers, token limits), and column mappings for claim data.
    *   `agent_configurations`: Define different named setups (e.g., `Default_No_Helper`, `Default_Fallacy_Helper`). Each setup specifies which LLM model to use for each agent (Persuader, Debater, Moderators) by referencing model names from `models.yaml`.

## Output and Results

### Single Run Output (`main.py`)

When running `main.py`, results are saved to:

*   **Debate Logs:** `debates/<topic_id>/<helper_type>/<chat_id>/`
    *   `debate_main.log`: Main debate transcript in JSONL format
    *   `debate_debug.log`: Debug logs in JSONL format
    *   `round_data.json`: Round-by-round debate data
*   **Summary File:** `all_debates_summary.xlsx` (in project root)
    *   Contains results for all debates run in the current session
    *   Includes columns: topic_id, claim, helper_type, result, rounds, finish_reason, conviction_rates_vector, feedback_tags_vector, argument_quality_rates_vector, debate_quality_rating, debate_quality_review, chat_id

### Batch Run Output (`multiple_runs.py`)

When running `multiple_runs.py`, all results are organized in:

*   **Results Directory:** `results/<timestamp>_<run_name>/`
    *   `debates/`: All debate logs for this batch run
    *   `all_debates_summary.xlsx`: Summary Excel file for this batch
    *   `settings.yaml`: Copy of settings used (for reproducibility)
    *   `prompts.zip`: Archive of prompts used (for reproducibility)
    *   `analysis/`: Analysis results (if analysis script runs automatically)

The `multiple_runs.py` script automatically runs the analysis script (`utils/analyze_debate_results.py`) after completion, generating visualizations and statistics in the `analysis/` subdirectory.

## Local LLMs

To use a local LLM:

1.  Ensure your local LLM server (e.g., Ollama, llama-cpp-python with API) is running.
2.  Define a configuration for it in `config/models.yaml` under `llm_models`.
    *   Set `provider: local`.
    *   Set `local_type: huggingface` (for Hugging Face models with quantization).
    *   Specify the `model_name_or_path` and `quantization_bits` (e.g., 4 for 4-bit quantization).
3.  Create a run configuration in `config/settings.yaml` under `agent_configurations` that references your local LLM model name.
4.  Run `main.py` or `multiple_runs.py` using the `--helper_type` option pointing to your local run configuration. 