# GUI Module Structure

This directory contains the refactored, componentized GUI application for the Beatlibrary Audio Provenance system.

## Architecture

The application has been refactored from a monolithic 2672-line file into a modular, maintainable structure following senior developer best practices.

## Module Structure

```
gui/
├── __init__.py              # Package exports
├── constants.py             # Configuration constants (colors, URLs, timeouts)
├── dialogs.py               # Custom alert and confirmation dialogs
├── theme.py                 # Theme configuration and UI component factories
├── api_client.py            # API client for backend communication
├── utils.py                 # Utility functions (logger, window styling, icon handling)
├── report_display.py        # Report formatting and display logic
├── visualizations.py        # Chart generation using matplotlib
├── main.py                  # Main application orchestrator
└── steps/
    ├── __init__.py          # Step component exports
    ├── step1_upload.py      # Step 1: Connection & File Upload
    ├── step2_processing.py  # Step 2: Processing Status
    └── step3_report.py      # Step 3: Report Display
```

## Component Responsibilities

### Core Modules

- **constants.py**: Centralized configuration (API URLs, colors, timeouts, window settings)
- **dialogs.py**: Custom dark-themed modal dialogs (CustomAlert, CustomConfirm)
- **theme.py**: Theme setup and reusable UI component factories (cards, buttons)
- **utils.py**: Cross-cutting utilities (Logger, window styling, icon management)

### Business Logic Modules

- **api_client.py**: Handles all API communication (upload, status checks, report downloads)
- **report_display.py**: Formats and displays provenance reports in various views
- **visualizations.py**: Generates matplotlib charts for data visualization

### UI Components

- **steps/step1_upload.py**: File upload interface with drag-and-drop, progress tracking
- **steps/step2_processing.py**: Processing status monitoring with job management
- **steps/step3_report.py**: Tabbed report display (Summary, Full Report, Visualizations, Logs)

### Orchestration

- **main.py**: Main application class that coordinates all components, manages state, and handles navigation

## Usage

### Running the Application

```python
from gui.main import main

if __name__ == "__main__":
    main()
```

Or use the entry point:

```bash
python gui_test_app_new.py
```

## Design Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Dependency Injection**: Components receive dependencies via constructor parameters
3. **Loose Coupling**: Components communicate through well-defined interfaces
4. **Reusability**: UI components and utilities can be easily reused
5. **Testability**: Each component can be tested independently
6. **Maintainability**: Changes to one component don't affect others

## Benefits of Refactoring

1. **Reduced Complexity**: 2672 lines → ~8 focused modules (~200-400 lines each)
2. **Improved Readability**: Each file has a clear purpose and scope
3. **Easier Maintenance**: Changes are localized to specific modules
4. **Better Testing**: Components can be unit tested independently
5. **Enhanced Collaboration**: Multiple developers can work on different modules
6. **Future Extensibility**: New features can be added as new modules or components

## Migration Notes

The original `gui_test_app.py` file is preserved for reference. The new modular structure maintains 100% feature parity while providing a much cleaner architecture.

