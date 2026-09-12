# Setup Sheet Generator Web

Browser-based conversion of the original Tkinter Setup Sheet Generator.

## Features

- Create a new setup sheet in the browser
- Load and edit an existing setup-sheet JSON file
- Setup fields for work holding, fixture details, drawing/revision, machine, program and times
- Add, edit and remove tool records
- Optional company logo upload for PDF branding
- Generate A4 setup-sheet PDFs in memory
- Download editable JSON files for later revision
- No hard-coded Mac file paths

## Deploy on Streamlit Community Cloud

1. Open Streamlit Community Cloud.
2. Create a new app from this repository.
3. Select branch `main`.
4. Set the main file path to `app.py`.
5. Deploy.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Project structure

```text
.
├── app.py
├── setup_sheet.py
├── requirements.txt
├── README.md
├── .gitignore
└── .streamlit/
    └── config.toml
```

The web version preserves the original data model (`user_inputs` and `tool_inputs`) so JSON files created by the original desktop app can be loaded into the web version.
