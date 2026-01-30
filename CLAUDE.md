# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains utility tools and API clients for internal use. Scripts are standalone Python utilities without a unified build system.

## Running Scripts

Scripts are run directly with Python:
```bash
python <script_name>.py
```

Example:
```bash
python get_my_calendar_today.py
python meeting_recorder_server.py  # Starts FastAPI server on port 8201
```

## Architecture

### API Client Pattern

API clients follow a consistent class-based pattern:
- `ApiNinjaBase` (api_ninja.py): Abstract base class with `_request()` method and `endpoint` property
- Subclasses implement `endpoint` property and `get()` method
- Example clients: `ApiNinjaFacts`, `JokeApi`, `UselessFact`

### Credential Loading

Two patterns are used:
1. **JSON credential file**: Load via constructor path parameter (e.g., `AinSlack("slack_credential.json")`)
2. **Environment variables**: Load via python-dotenv (e.g., `API_NINJA_KEY` in `.env`)

### Main Function Convention

All scripts include a `main()` function that serves dual purpose:
1. Prints usage examples showing how to instantiate and use the class
2. Runs a simple test/demo of the functionality

### Key Components

- `AinSlack`: Slack messaging wrapper using slack_sdk
- `meeting_recorder_server.py`: FastAPI server combining Whisper (speech-to-text) and Ollama (text summarization), runs on GPU 3
- `get_my_calendar_today.py`: Google Calendar integration using OAuth tokens

## Dependencies

Required packages (install as needed):
- `slack_sdk` - Slack API
- `python-dotenv` - Environment variable loading
- `requests` - HTTP client
- `google-auth`, `google-auth-oauthlib`, `google-api-python-client` - Google Calendar
- `fastapi`, `uvicorn` - Meeting recorder server
- `whisper` - Speech recognition
- `pytz` - Timezone handling

## Custom Slash Command

`/py-class` - Generates a Python class file from a template with credential loading pattern and main() test function
