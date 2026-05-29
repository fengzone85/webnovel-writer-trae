#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shell 自动补全脚本生成器
"""

import argparse
import sys
from pathlib import Path


BASH_COMPLETION = '''#!/bin/bash
# Webnovel Writer Bash Completion

_webnovel_cli()
{
    local cur prev words cword
    _init_completion || return

    case $prev in
        init)
            COMPREPLY=( $(compgen -W "--name --genre --character --finger --help" -- "$cur") )
            return
            ;;
        plan|write|review|commit|task)
            COMPREPLY=( $(compgen -W "$(seq 1 100)" -- "$cur") )
            return
            ;;
        preflight)
            COMPREPLY=( $(compgen -W "--format --json --verbose" -- "$cur") )
            return
            ;;
        backup)
            COMPREPLY=( $(compgen -W "create list restore archive stats clean help" -- "$cur") )
            return
            ;;
        deconstruct|learn)
            _filedir
            return
            ;;
        dashboard)
            COMPREPLY=( $(compgen -W "--port --host --debug" -- "$cur") )
            return
            ;;
        query)
            COMPREPLY=( $(compgen -W "--type --keyword" -- "$cur") )
            return
            ;;
        status|events|memory)
            return
            ;;
    esac

    if [[ $cword -eq 1 ]] ; then
        COMPREPLY=( $(compgen -W "init status preflight plan write review query commit events task \\
            dashboard deconstruct learn import export backup db reader-pull memory help" -- "$cur") )
    fi
}

complete -F _webnovel_cli webnovel_cli.py
complete -F _webnovel_cli python webnovel_cli.py
'''

ZSH_COMPLETION = '''#!/usr/zsh
# Webnovel Writer Zsh Completion

_webnovel_cli() {
    local -a commands
    commands=(
        'init:Initialize new project'
        'status:Show project status'
        'preflight:Run health check'
        'plan:Plan volume outline'
        'write:Write chapter'
        'review:Review chapter'
        'commit:Commit chapter'
        'task:Get writing task'
        'dashboard:Start dashboard'
        'deconstruct:Deconstruct reference'
        'learn:Learn from reference'
        'import:Import data'
        'export:Export data'
        'backup:Backup management'
        'db:Database management'
        'query:Query information'
        'memory:Memory management'
        'reader-pull:Reader pull analysis'
    )

    _describe 'command' commands
}

compdef _webnovel_cli webnovel_cli.py
'''

FISH_COMPLETION = '''#!/usr/bin/env fish
# Webnovel Writer Fish Completion

complete -c webnovel_cli.py -f

# Main commands
complete -c webnovel_cli.py -n '__fish_use_subcommand' -a 'init' -d 'Initialize new project'
complete -c webnovel_cli.py -n '__fish_use_subcommand' -a 'status' -d 'Show project status'
complete -c webnovel_cli.py -n '__fish_use_subcommand' -a 'preflight' -d 'Run health check'
complete -c webnovel_cli.py -n '__fish_use_subcommand' -a 'plan' -d 'Plan volume outline'
complete -c webnovel_cli.py -n '__fish_use_subcommand' -a 'write' -d 'Write chapter'
complete -c webnovel_cli.py -n '__fish_use_subcommand' -a 'review' -d 'Review chapter'
complete -c webnovel_cli.py -n '__fish_use_subcommand' -a 'commit' -d 'Commit chapter'
complete -c webnovel_cli.py -n '__fish_use_subcommand' -a 'task' -d 'Get writing task'
complete -c webnovel_cli.py -n '__fish_use_subcommand' -a 'dashboard' -d 'Start dashboard'
complete -c webnovel_cli.py -n '__fish_use_subcommand' -a 'backup' -d 'Backup management'
complete -c webnovel_cli.py -n '__fish_use_subcommand' -a 'memory' -d 'Memory management'
complete -c webnovel_cli.py -n '__fish_use_subcommand' -a 'query' -d 'Query information'
complete -c webnovel_cli.py -n '__fish_use_subcommand' -a 'learn' -d 'Learn from reference'
complete -c webnovel_cli.py -n '__fish_use_subcommand' -a 'deconstruct' -d 'Deconstruct reference'
complete -c webnovel_cli.py -n '__fish_use_subcommand' -a 'import' -d 'Import data'
complete -c webnovel_cli.py -n '__fish_use_subcommand' -a 'export' -d 'Export data'

# Command options
complete -c webnovel_cli.py -n '__fish_seen_subcommand_from init' -l name -d 'Project name'
complete -c webnovel_cli.py -n '__fish_seen_subcommand_from init' -l genre -d 'Genre type'
complete -c webnovel_cli.py -n '__fish_seen_subcommand_from init' -l character -d 'Main character'
complete -c webnovel_cli.py -n '__fish_seen_subcommand_from dashboard' -l port -d 'Port number'
complete -c webnovel_cli.py -n '__fish_seen_subcommand_from preflight' -l format -d 'Output format'
complete -c webnovel_cli.py -n '__fish_seen_subcommand_from backup' -a 'create' -d 'Create backup'
complete -c webnovel_cli.py -n '__fish_seen_subcommand_from backup' -a 'list' -d 'List backups'
complete -c webnovel_cli.py -n '__fish_seen_subcommand_from backup' -a 'restore' -d 'Restore backup'
complete -c webnovel_cli.py -n '__fish_seen_subcommand_from backup' -a 'archive' -d 'Archive old backups'
'''


def generate_completion_scripts(output_dir: Path):
    """生成补全脚本"""
    output_dir.mkdir(parents=True, exist_ok=True)

    bash_file = output_dir / "webnovel_cli.bash"
    zsh_file = output_dir / "webnovel_cli.zsh"
    fish_file = output_dir / "webnovel_cli.fish"

    bash_file.write_text(BASH_COMPLETION, encoding='utf-8')
    zsh_file.write_text(ZSH_COMPLETION, encoding='utf-8')
    fish_file.write_text(FISH_COMPLETION, encoding='utf-8')

    print(f"Generated completion scripts:")
    print(f"  - {bash_file}")
    print(f"  - {zsh_file}")
    print(f"  - {fish_file}")
    print()
    print("To use:")
    print("  Bash: source webnovel_cli.bash >> ~/.bashrc")
    print("  Zsh:  source webnovel_cli.zsh >> ~/.zshrc")
    print("  Fish: cp webnovel_cli.fish ~/.config/fish/completions/")


def main():
    parser = argparse.ArgumentParser(description="Generate shell completion scripts")
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path(__file__).parent.parent.parent / "completions",
        help="Output directory"
    )
    args = parser.parse_args()

    generate_completion_scripts(args.output)


if __name__ == "__main__":
    main()
