#!/bin/sh
set -e

# Color codes
GRAY='\033[0;90m'
NC='\033[0m' # No Color

log() {
    printf "install.sh: %s\n" "$1"
}

log_grey() {
    printf "${GRAY}install.sh: %s${NC}\n" "$1" >&2
}

err() {
    if [ ! -z $td ]; then
        rm -rf $td
    fi

    log_grey "ERROR $1"
    exit 1
}

need() {
    if ! command -v $1 >/dev/null 2>&1; then
        err "need $1 (command not found)"
    fi
}

help() {
    echo "Usage: install.sh [options]"
    echo ""
    echo "Options:"
    echo "  --update, -u       Update to latest or specified version"
    echo "  --version VER      Install version VER"
    echo "  --target TARGET    Install for target platform TARGET"
    echo "  --to DEST          Install to DEST"
    echo "  --help, -h         Show this help text"
}

update=false
while test $# -gt 0; do
    case $1 in
    --update | -u)
        update=true
        ;;
    --help | -h)
        help
        exit 0
        ;;
    --version)
        version=$2
        shift
        ;;
    --package | -p)
        package=$2
        shift
        ;;
    --target)
        target=$2
        shift
        ;;
    --to)
        dest=$2
        shift
        ;;
    *) ;;

    esac
    shift
done

# Set default package if not specified
package="${package:-dbt}"

# Dependencies
need basename
need curl
need install
need mkdir
need mktemp
need tar

# Optional dependencies
if [ -z $version ] || [ -z $target ]; then
    need cut
fi

if [ -z $version ]; then
    need rev
fi

if [ -z $target ]; then
    need grep
fi

if [ -z "${dest:-}" ]; then
    dest="$HOME/.local/bin"
else
    # Convert relative path to absolute
    case "$dest" in
        /*) ;; # Already absolute path
        *) dest="$PWD/$dest" ;; # Convert relative to absolute
    esac
fi

# Function to format install output in grey
format_install_output() {
    while IFS= read -r line; do
        printf "${GRAY}%s${NC}\n" "$line" >&2
    done
}

# Check version of an installed binary
# Usage: check_binary_version binary_path binary_name
# Returns: version string if found, empty string if not found
check_binary_version() {
    local binary_path="$1"
    local binary_name="$2"
    local version=""

    if [ -f "$binary_path" ] && [ -x "$binary_path" ]; then
        version=$("$binary_path" --version 2>/dev/null | cut -d ' ' -f 2 || echo "")
        if [ ! -z "$version" ]; then
            log_grey "Current installed $binary_name version: $version"
        fi
    fi

    echo "$version"
}

# Compare installed version with target version
# Usage: compare_versions current_version target_version is_latest
# Returns: 0 if versions match, 1 if they don't match
compare_versions() {
    local current_version="$1"
    local target_version="$2"
    local version="$3"
    local package="$4"

    if [ "$current_version" = "$target_version" ]; then
        if [ -z "$version" ]; then
            log "Latest $package version $target_version is already installed"
        else
            log "$package version $target_version is already installed"
        fi
        return 0
    fi

    return 1
}

# Detect and set target platform
# Usage: detect_target
# Returns: target platform string
detect_target() {
    local cpu_arch_target=$(uname -m)
    local operating_system=$(uname -s | tr '[:upper:]' '[:lower:]')
    local target=""

    if [ "$operating_system" = "linux" ]; then
        if [ -n "$(ldd --version 2>/dev/null)" ]; then
            if [ "$cpu_arch_target" = "arm64" ] || [ "$cpu_arch_target" = "aarch64" ]; then
                target="aarch64-unknown-linux-gnu"
            elif [ "$cpu_arch_target" = "x86_64" ]; then
                target="x86_64-unknown-linux-gnu"
            else
                err "Unsupported CPU Architecture: $cpu_arch_target"
            fi
        else
            if [ "$cpu_arch_target" = "x86_64" ]; then
                target="x86_64-unknown-linux-gnu"
            else
                err "Unsupported CPU Architecture: $cpu_arch_target"
            fi
        fi
    elif [ "$operating_system" = "darwin" ]; then
        if [ "$cpu_arch_target" = "arm64" ]; then
            target="aarch64-apple-darwin"
        else
            target="x86_64-apple-darwin"
        fi
    else
        err "Unsupported OS: $operating_system"
    fi

    log_grey "Target: $target"
    echo "$target"
}

show_path_instructions() {
    log_grey ""
    log_grey "NOTE: $dest may not be in your PATH."
    log_grey "To add it permanently, run one of these commands depending on your shell:"
    log_grey "  For bash/zsh: echo 'export PATH=\"\$PATH:$dest\"' >> ~/.bashrc  # or ~/.zshrc"
    log_grey ""
    log_grey "To use dbt in this session immediately, run:"
    log_grey "    export PATH=\"\$PATH:$dest\""
    log_grey ""
    log_grey "Then restart your terminal or run 'source ~/.bashrc' (or equivalent) for permanent changes"
}

# Setup shell config file and PATH
# Usage: setup_shell_config dest_path
setup_shell_config() {
    local dest="$1"
    local config_file=""
    local shell_name=""

    # Detect shell and config file early
    if [ -n "$SHELL" ]; then
        shell_name=$(basename "$SHELL")
    else
        if [ -f "$HOME/.bashrc" ]; then
            shell_name="bash"
        elif [ -f "$HOME/.profile" ]; then
            shell_name="sh"
        else
            shell_name=$(ps -p $PPID -o comm= | sed 's/.*\///')
        fi
    fi

    # Set config file based on shell
    if [ "$shell_name" = "zsh" ]; then
        config_file="$HOME/.zshrc"
    elif [ "$shell_name" = "bash" ]; then
        config_file="$HOME/.bashrc"
    elif [ "$shell_name" = "fish" ]; then
        config_file="$HOME/.config/fish/config.fish"
    fi

    if [ -z "$config_file" ]; then
        log_grey "NOTE: Failed to identify config file."
        show_path_instructions
        return 1
    fi

    # check if the config file exists or not and create it if it doesn't
    if [ ! -f "$config_file" ]; then
        if touch "$config_file"; then
            log_grey "Created config file $config_file"
        else
            log_grey "Note: Failed to create config file $config_file.  You will need to manually update your PATH."
            return 1
        fi
    fi

    local needs_config_path_update=false
    if ! grep -q "export PATH=\"\$PATH:$dest\"" "$config_file" 2>/dev/null; then
        needs_config_path_update=true
    fi

    local needs_path_update=false
    if ! echo "$PATH" | grep -q "$dest"; then
        needs_path_update=true
    fi

    # Check if aliases need to be updated
    local needs_alias_update=false
    if ! grep -q "alias dbtf=$dest/dbt" "$config_file" 2>/dev/null; then
        needs_alias_update=true
    fi

    if [ "$shell_name" != "fish" ]; then
        if [ "$needs_config_path_update" = true ]; then
            {
                echo "" >> "$config_file" && \
                echo "# Added by dbt installer" >> "$config_file" && \
                echo "export PATH=\"\$PATH:$dest\"" >> "$config_file" && \
                log_grey "Added $dest to PATH in $config_file"
            } || {
                log "NOTE: Failed to modify $config_file."
                show_path_instructions
                return 1
            }
        fi
    else
        if [ "$needs_config_path_update" = true ]; then
            {
                echo "fish_add_path $dest" >> "$config_file"
                log_grey "Added $dest to PATH in $config_file"
            } || {
                log_grey "NOTE: Failed to modify $config_file."
                show_path_instructions
                return 1
            }
        fi
    fi

    if [ "$needs_path_update" = true ]; then
        log "To use dbt in this session, run:" && \
        log "    source $config_file" && \
        log "" && \
        log "The PATH change will be permanent for new terminal sessions."
    fi

    # Handle alias updates separately
    if [ "$needs_alias_update" = true ]; then
        {
            echo "" >> "$config_file" && \
            echo "# dbt aliases" >> "$config_file" && \
            echo "alias dbtf=$dest/dbt" >> "$config_file" && \
            log "Added alias dbtf to $config_file" && \
            log "To run with dbtf in this session, run: source $config_file"
        } || {
            log_grey "NOTE: Failed to add aliases to $config_file."
            return 1
        }
    fi

    return 0
}

# Determine version to install
# Usage: determine_version [specific_version]
# Returns: target version string
determine_version() {
    local specific_version="$1"
    local target_version=""
    version_url="https://public.cdn.getdbt.com/fs/versions.json"

    versions=$(curl -s "$version_url")

    if [ -z "$specific_version" ];then
        log_grey "Checking for latest version"
        target_version=$(echo "$versions" | jq -r ".latest.tag" | sed 's/^v//')
        log_grey "$specific_version available version: $target_version"
    elif echo "$versions" | jq -e "has(\"$specific_version\")" > /dev/null;then
        log_grey "Checking for $specific_version version"
        target_version=$(echo "$versions" | jq -r ".\"$specific_version\".tag" | sed 's/^v//')
        log_grey "$specific_version available version: $target_version"
    else
        target_version="$specific_version"
        log_grey "Requested version: $target_version"
    fi
    echo "$target_version"
}

# Display ASCII art for a package
# Usage: display_ascii_art package_name version
display_ascii_art() {
    local package_name="$1"
    local version="$2"

    if [ "$package_name" = "dbt" ]; then
        cat<<EOF

 =====              =====    â”“â”“  
=========        =========  â”â”«â”£â”“â•‹
 ===========    >========   â”—â”»â”—â”›â”—
  ======================    â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—â–ˆâ–ˆâ•—   â–ˆâ–ˆâ•—â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—â–ˆâ–ˆâ•— â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•— â–ˆâ–ˆâ–ˆâ•—   â–ˆâ–ˆâ•—
   ====================     â–ˆâ–ˆâ•”â•â•â•â•â•â–ˆâ–ˆâ•‘   â–ˆâ–ˆâ•‘â–ˆâ–ˆâ•”â•â•â•â•â•â–ˆâ–ˆâ•‘â–ˆâ–ˆâ•”â•â•â•â–ˆâ–ˆâ•—â–ˆâ–ˆâ–ˆâ–ˆâ•—  â–ˆâ–ˆâ•‘
    ========--========      â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—  â–ˆâ–ˆâ•‘   â–ˆâ–ˆâ•‘â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—â–ˆâ–ˆâ•‘â–ˆâ–ˆâ•‘   â–ˆâ–ˆâ•‘â–ˆâ–ˆâ•”â–ˆâ–ˆâ•— â–ˆâ–ˆâ•‘
     =====-    -=====       â–ˆâ–ˆâ•”â•â•â•  â–ˆâ–ˆâ•‘   â–ˆâ–ˆâ•‘â•šâ•â•â•â•â–ˆâ–ˆâ•‘â–ˆâ–ˆâ•‘â–ˆâ–ˆâ•‘   â–ˆâ–ˆâ•‘â–ˆâ–ˆâ•‘â•šâ–ˆâ–ˆâ•—â–ˆâ–ˆâ•‘
    ========--========      â–ˆâ–ˆâ•”â•â•â•  â–ˆâ–ˆâ•‘   â–ˆâ–ˆâ•‘â•šâ•â•â•â•â–ˆâ–ˆâ•‘â–ˆâ–ˆâ•‘â–ˆâ–ˆâ•‘   â–ˆâ–ˆâ•‘â–ˆâ–ˆâ•‘â•šâ–ˆâ–ˆâ•—â–ˆâ–ˆâ•‘
   ====================     â–ˆâ–ˆâ•‘     â•šâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•”â•â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•‘â–ˆâ–ˆâ•‘â•šâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•”â•â–ˆâ–ˆâ•‘ â•šâ–ˆâ–ˆâ–ˆâ–ˆâ•‘
  ======================    â•šâ•â•      â•šâ•â•â•â•â•â• â•šâ•â•â•â•â•â•â•â•šâ•â• â•šâ•â•â•â•â•â• â•šâ•â•  â•šâ•â•â•â•
 ========<   ============                        â”Œâ”€â”â”Œâ”â”Œâ”Œâ”€â”â”¬â”Œâ”â”Œâ”Œâ”€â”
=========      ==========                        â”œâ”¤ â”‚â”‚â”‚â”‚ â”¬â”‚â”‚â”‚â”‚â”œâ”¤ 
 =====             =====                         â””â”€â”˜â”˜â””â”˜â””â”€â”˜â”´â”˜â””â”˜â””â”€â”˜ $version

EOF
    else
        log "Successfully installed $package_name $version to: $dest"
    fi
}

# Install a package
# Usage: install_package package_name version target dest update
# Returns: 0 on success, 1 on failure
install_package() {
    local package_name="$1"
    local version="$2"
    local target="$3"
    local dest="$4"
    local update="$5"
    local td=""
    local url=""
    local current_version=""

    # Check if already installed and get version
    current_version=$(check_binary_version "$dest/$package_name" "$package_name")
    if [ -n "$current_version" ] && [ "$current_version" = "$version" ]; then
        log "$package_name version $version is already installed"
        return 0
    fi

    # If we get here, version is different, so check if we can proceed
    if [ -e "$dest/$package_name" ] && [ "$update" = false ]; then
        err "$package_name already exists in $dest, use the --update flag to reinstall"
        return 1
    fi

    log "Installing $package_name to: $dest"
    # Create the directory if it doesn't exist
    mkdir -p "$dest"

    # Create temp directory
    td=$(mktemp -d || mktemp -d -t tmp)

    # Construct URL based on package
    case "$package_name" in
        "dbt")
            url="https://public.cdn.getdbt.com/fs/cli/fs-v$version-$target.tar.gz"
            ;;
        "dbt-lsp")
            url="https://public.cdn.getdbt.com/fs/lsp/fs-lsp-v$version-$target.tar.gz"
            ;;
        *)
            err "Invalid package name: $package_name"
            return 1
            ;;
    esac

    log_grey "Downloading: $url"
    # Check if URL exists and returns valid content
    if ! curl -sL -f -o /dev/null "$url"; then
        err "Failed to download package from $url. Verify you are requesting a valid version on a supported platform."
        return 1
    fi

    # Now download and extract
    if ! curl -sL "$url" | tar -C "$td" -xz; then
        err "Failed to extract package. The downloaded archive appears to be invalid."
        return 1
    fi

    # Check if any files were extracted
    if [ -z "$(ls -A "$td")" ]; then
        err "No files were extracted from the archive"
        return 1
    fi

    for f in $(cd "$td" && find . -type f); do
        test -x "$td/$f" || {
            log_grey "File $f is not executable, skipping"
            continue
        }

        if [ -e "$dest/$package_name" ] && [ "$update" = true ]; then
            # Remove file - no sudo needed for home directory
            rm -f "$dest/$package_name" || {
                err "Error: Failed to remove existing $package_name binary."
                return 1
            }
        fi

        log_grey "Moving $f to $dest/$package_name"
        # No sudo needed for home directory
        mkdir -p "$dest" && install -v -m 755 "$td/$f" "$dest/$package_name" 2>&1 | format_install_output || {
            err "Error: Failed to install $package_name binary."
            return 1
        }
    done

    display_ascii_art "$package_name" "$version"

    rm -rf "$td"
    return 0
}

# Install packages based on selection
# Usage: install_packages package target_version target dest update
# Returns: 0 on success, 1 on failure
install_packages() {
    local package="$1"
    local target_version="$2"
    local target="$3"
    local dest="$4"
    local update="$5"
    local current_dbt_version=""
    local current_lsp_version=""
    local dbt_needs_update=false
    local lsp_needs_update=false

    # Check if versions match
    if [ "$package" = "all" ] || [ "$package" = "dbt" ]; then
        current_dbt_version=$(check_binary_version "$dest/dbt" "dbt")
        if ! compare_versions "$current_dbt_version" "$target_version" "$version" "dbt"; then
            dbt_needs_update=true
        fi
    fi

    if [ "$package" = "all" ] || [ "$package" = "dbt-lsp" ]; then
        current_lsp_version=$(check_binary_version "$dest/dbt-lsp" "dbt-lsp")
        if ! compare_versions "$current_lsp_version" "$target_version" "$version" "dbt-lsp"; then
            lsp_needs_update=true
        fi
    fi

    # Exit if no updates needed
    if [ "$dbt_needs_update" = false ] && [ "$lsp_needs_update" = false ]; then
        return 0
    fi

    # Install packages
    if ([ "$package" = "all" ] || [ "$package" = "dbt" ]) && [ "$dbt_needs_update" = true ]; then
        if ! install_package "dbt" "$target_version" "$target" "$dest" "$update"; then
            return 1
        fi
    fi

    if ([ "$package" = "all" ] || [ "$package" = "dbt-lsp" ]) && [ "$lsp_needs_update" = true ]; then
        if ! install_package "dbt-lsp" "$target_version" "$target" "$dest" "$update"; then
            return 1
        fi
    fi

    # Setup shell config only for dbt
    if [ "$package" = "all" ] || [ "$package" = "dbt" ]; then
        setup_shell_config "$dest"
    fi

    return 0
}

validate_versions() {
    local dest="$1"

    dbt_path="$dest/dbt"
    lsp_path="$dest/dbt-lsp"

    if [ -f "$dbt_path" ] && [ -x "$dbt_path" ]; then
        dbt_version=$("$dbt_path" --version 2>/dev/null | cut -d ' ' -f 2 || echo "")
    fi

    if [ -f "$lsp_path" ] && [ -x "$lsp_path" ]; then
        lsp_version=$("$lsp_path" --version 2>/dev/null | cut -d ' ' -f 2 || echo "")
    fi

    if [ -z "$dbt_version" ] || [ -z "$lsp_version" ]; then
        # if both aren't installed, nothing to compare
        return 0
    fi

    if [ "$dbt_version" != "$lsp_version" ]; then
        log_grey "WARNING: dbt and dbt-lsp versions do not match"
    fi

    return 0
}


# Determine version to install
target_version=$(determine_version "$version")

target="${target:-$(detect_target)}"

install_packages "$package" "$target_version" "$target" "$dest" "$update"

validate_versions "$dest"