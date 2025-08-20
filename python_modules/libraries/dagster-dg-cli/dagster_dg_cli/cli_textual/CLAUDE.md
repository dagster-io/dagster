# CLI Textual Module Instructions

## Testing Restrictions

**IMPORTANT**: Do not try to launch these commands from Claude:
- `dg scaffold branch` (without arguments - will hang waiting for interactive input)
- `dg scaffold branch --web` (will attempt to launch web interface)
- `dg-web scaffold branch` (without arguments - will hang waiting for interactive input)  
- `dg-web scaffold branch --web` (will attempt to launch web interface)
- `textual-web` (any variant - will launch web server)
- `python -m textual` (any variant - will launch interactive textual interface or TUI)
- `textual run --dev` (will launch textual development server)

These commands require interactive input or web browser launching which cannot be properly tested in the Claude environment.

## Safe Testing Commands

These are safe to test:
- `dg scaffold branch "description"` (with description argument)
- `dg-web scaffold branch "description"` (with description argument)
- `dg scaffold branch --help`
- `dg-web scaffold branch --help`
- `textual-web --help` (help only)