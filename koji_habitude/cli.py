"""
koji-habitude - cli

Main CLI interface using clique with orchestration of the synchronization process.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import sys
from pathlib import Path
from typing import Optional, List, Tuple

import clique

from .templates import create_template_registry
from .loader import load_object_data, print_load_summary
from .object_map import ObjectMap, OnlineResolver, OfflineResolver
from .resolver import resolve_tiers, detect_circular_dependencies
from .koji_client import create_koji_client


def collect_templates_and_data(data_paths: List[str], templates_path: Optional[str]) -> Tuple[dict, List[str]]:
    """
    Collect templates and data directories from arguments.
    
    DATA paths are loaded for all object types (including templates).
    --templates path is loaded ONLY for templates (no other object types).
    
    Args:
        data_paths: List of data directories/files
        templates_path: Optional templates-only path
        
    Returns:
        Tuple of (templates_dict, data_directories)
    """
    
    # Collect data directories (for loading all object types)
    data_dirs = []
    
    for path_str in data_paths:
        path = Path(path_str)
        if path.is_dir():
            data_dirs.append(path_str)
        elif path.is_file():
            # Single file - parent directory goes to data
            parent_dir = str(path.parent)
            if parent_dir not in data_dirs:
                data_dirs.append(parent_dir)
                
    # Load templates from DATA paths (they contain all object types including templates)
    all_templates = {}
    for data_dir in data_dirs:
        try:
            templates = create_template_registry(data_dir)
            all_templates.update(templates)
        except FileNotFoundError:
            # Skip missing directories
            continue
            
    # Load additional templates from explicit --templates path (templates-only)
    if templates_path:
        try:
            templates = create_template_registry(templates_path)
            all_templates.update(templates)
        except FileNotFoundError:
            print(f"Warning: Templates path not found: {templates_path}")
            
    return all_templates, data_dirs


@clique.command()
@clique.option('--templates', metavar='PATH', help="Location to find templates that are not available in DATA")
@clique.option('--profile', help="Koji profile to use for connection")
@clique.option('--offline', is_flag=True, help="Run in offline mode (no koji connection)")
@clique.option('--dry-run', is_flag=True, help="Show what would be done without making changes")
@clique.argument('data', nargs=-1, required=True, metavar='DATA')
def sync(templates: Optional[str], profile: Optional[str], offline: bool, dry_run: bool, data: Tuple[str, ...]):
    """
    Synchronize koji data with hub instance.
    
    This command loads templates and data files, resolves dependencies,
    and applies changes to the koji hub in the correct order.
    
    DATA can be directories or files containing YAML object definitions.
    """
    
    try:
        data_list = list(data)
        
        # Collect templates and data
        print(f"Loading templates and data from: {', '.join(data_list)}")
        if templates:
            print(f"Additional templates from: {templates}")
            
        all_templates, data_dirs = collect_templates_and_data(data_list, templates)
        print(f"Loaded {len(all_templates)} templates")
        
        # Set up resolver based on mode
        if offline:
            print("Running in offline mode")
            resolver = OfflineResolver()
        else:
            print(f"Using koji profile: {profile or 'default'}")
            resolver = OnlineResolver(profile)
            
        # Create object map and load data
        obj_map = ObjectMap(resolver)
        for data_dir in data_dirs:
            print(f"Loading data from {data_dir}")
            load_object_data(data_dir, all_templates, obj_map)
        
        # Print summary of loaded objects
        print_load_summary(obj_map)
        
        # Check for circular dependencies
        cycles = detect_circular_dependencies(obj_map)
        if cycles:
            print(f"\nError: Found {len(cycles)} circular dependencies:")
            for i, cycle in enumerate(cycles, 1):
                cycle_str = " -> ".join(f"{t}:{n}" for t, n in cycle)
                print(f"  {i}. {cycle_str}")
            return 1
            
        # Resolve dependency tiers
        print("\nResolving dependency tiers...")
        tiers = resolve_tiers(obj_map)
        print(f"Resolved {len(tiers)} tiers")
        
        for i, tier in enumerate(tiers, 1):
            print(f"  Tier {i}: {len(tier)} objects")
            
        # Show missing objects if in offline mode
        if offline and isinstance(resolver, OfflineResolver):
            missing = resolver.get_missing_objects()
            if missing:
                print(f"\nWarning: {len(missing)} missing dependencies:")
                for obj_type, obj_name in missing:
                    print(f"  {obj_type}: {obj_name}")
                    
        # Process tiers
        if dry_run:
            print("\nDry run mode - no changes will be made")
            return 0
            
        if offline:
            print("\nOffline mode - skipping koji operations")
            return 0
            
        # Connect to koji and process tiers
        print("\nConnecting to koji...")
        with create_koji_client(profile) as koji_client:
            for i, tier in enumerate(tiers, 1):
                print(f"\nProcessing tier {i}...")
                koji_client.process_object_tier(tier)
                
        print("\nSynchronization completed successfully")
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        if '--debug' in sys.argv:
            import traceback
            traceback.print_exc()
        return 1


@clique.command()
@clique.option('--templates', metavar='PATH', help="Location to find templates that are not available in DATA")
@clique.option('--profile', help="Koji profile to use for connection")
@clique.option('--offline', is_flag=True, help="Run in offline mode (no koji connection)")
@clique.argument('data', nargs=-1, required=True, metavar='DATA')
def diff(templates: Optional[str], profile: Optional[str], offline: bool, data: Tuple[str, ...]):
    """
    Show what changes would be made without applying them.
    
    This is a convenience alias for 'sync --dry-run'.
    
    DATA can be directories or files containing YAML object definitions.
    """
    
    # Call sync with dry_run=True
    return sync(templates, profile, offline, True, data)


@clique.command()
@clique.argument('paths', nargs=-1, required=True, metavar='PATH')
def list_templates(paths: Tuple[str, ...]):
    """
    List available templates.
    
    Shows all templates found in the given locations with their configuration details.
    
    PATH can be directories containing template files.
    """
    
    try:
        all_templates = {}
        paths_list = list(paths)
        
        # Load templates from all provided paths
        for path_str in paths_list:
            try:
                templates = create_template_registry(path_str)
                print(f"Loading templates from {path_str}")
                for name, template in templates.items():
                    if name in all_templates:
                        print(f"  Warning: Template '{name}' found in multiple locations, using latest")
                    all_templates[name] = template
            except FileNotFoundError:
                print(f"Warning: Path not found: {path_str}")
                continue
            except Exception as e:
                print(f"Error loading templates from {path_str}: {e}")
                continue
        
        if not all_templates:
            print("No templates found")
            return 0
            
        print(f"\nFound {len(all_templates)} templates:")
        for name in sorted(all_templates.keys()):
            template = all_templates[name]
            print(f"  {name}")
            if template.schema:
                print("    Schema: configured")
            if template.template_file:
                print(f"    File: {template.template_file}")
            else:
                print("    Inline template")
                
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


@clique.command()
@clique.option('--templates', metavar='PATH', help="Location to find templates that are not available in DATA")
@clique.argument('data', nargs=-1, required=True, metavar='DATA')
def validate(templates: Optional[str], data: Tuple[str, ...]):
    """
    Validate data files and templates.
    
    Loads and validates all templates and data files without connecting to koji.
    
    DATA can be directories or files containing YAML object definitions.
    """
    
    try:
        data_list = list(data)
        
        # Collect templates and data
        print(f"Validating templates and data from: {', '.join(data_list)}")
        if templates:
            print(f"Additional templates from: {templates}")
            
        all_templates, data_dirs = collect_templates_and_data(data_list, templates)
        print(f"✓ Loaded {len(all_templates)} templates")
        
        # Load data with offline resolver
        resolver = OfflineResolver()
        obj_map = ObjectMap(resolver)
        
        for data_dir in data_dirs:
            print(f"Validating data from {data_dir}")
            load_object_data(data_dir, all_templates, obj_map)
        print(f"✓ Loaded {len(obj_map)} objects")
        
        # Check for circular dependencies
        cycles = detect_circular_dependencies(obj_map)
        if cycles:
            print(f"✗ Found {len(cycles)} circular dependencies:")
            for i, cycle in enumerate(cycles, 1):
                cycle_str = " -> ".join(f"{t}:{n}" for t, n in cycle)
                print(f"  {i}. {cycle_str}")
            return 1
        else:
            print("✓ No circular dependencies found")
            
        # Resolve tiers
        tiers = resolve_tiers(obj_map)
        print(f"✓ Resolved {len(tiers)} dependency tiers")
        
        # Show missing dependencies
        missing = resolver.get_missing_objects()
        if missing:
            print(f"⚠ {len(missing)} missing dependencies (expected in koji):")
            for obj_type, obj_name in missing:
                print(f"  {obj_type}: {obj_name}")
        else:
            print("✓ No missing dependencies")
            
        print("\nValidation completed successfully")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


@clique.group()
def main():
    """
    koji-habitude - Synchronize local koji data expectations with hub instance.
    
    This tool loads YAML templates and data files, resolves dependencies,
    and applies changes to a koji hub in the correct order.
    """
    
    pass


# Register subcommands
main.add_command(sync)
main.add_command(diff)
main.add_command(list_templates)
main.add_command(validate)


if __name__ == '__main__':
    sys.exit(main())

# The end.