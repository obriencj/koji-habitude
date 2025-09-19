"""
koji-habitude - cli

Main CLI interface using clique with orchestration of the synchronization process.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import sys
from pathlib import Path
from typing import Optional

import clique

from .templates import create_template_registry
from .loader import load_object_data, print_load_summary
from .object_map import ObjectMap, OnlineResolver, OfflineResolver
from .resolver import resolve_tiers, detect_circular_dependencies
from .koji_client import create_koji_client


@clique.command()
@clique.option('--koji-profile', help="Koji profile to use for connection")
@clique.option('--templates-path', required=True, help="Path to templates directory")
@clique.option('--data-dir', required=True, help="Path to data directory")
@clique.option('--offline', is_flag=True, help="Run in offline mode (no koji connection)")
@clique.option('--dry-run', is_flag=True, help="Show what would be done without making changes")
def sync(koji_profile: Optional[str], templates_path: str, data_dir: str, offline: bool, dry_run: bool):
    """
    Synchronize koji data with hub instance.
    
    This command loads templates and data files, resolves dependencies,
    and applies changes to the koji hub in the correct order.
    """
    
    try:
        # Load templates
        print(f"Loading templates from {templates_path}")
        templates = create_template_registry(templates_path)
        print(f"Loaded {len(templates)} templates")
        
        # Set up resolver based on mode
        if offline:
            print("Running in offline mode")
            resolver = OfflineResolver()
        else:
            print(f"Using koji profile: {koji_profile or 'default'}")
            resolver = OnlineResolver(koji_profile)
            
        # Create object map and load data
        obj_map = ObjectMap(resolver)
        print(f"Loading data from {data_dir}")
        load_object_data(data_dir, templates, obj_map)
        
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
        with create_koji_client(koji_profile) as koji_client:
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
@clique.option('--templates-path', required=True, help="Path to templates directory")
def list_templates(templates_path: str):
    """
    List available templates.
    
    Shows all templates found in the templates directory.
    """
    
    try:
        templates = create_template_registry(templates_path)
        
        if not templates:
            print("No templates found")
            return 0
            
        print(f"Found {len(templates)} templates:")
        for name in sorted(templates.keys()):
            template = templates[name]
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
@clique.option('--data-dir', required=True, help="Path to data directory")
@clique.option('--templates-path', required=True, help="Path to templates directory")
def validate(data_dir: str, templates_path: str):
    """
    Validate data files and templates.
    
    Loads and validates all templates and data files without connecting to koji.
    """
    
    try:
        # Load templates
        print(f"Validating templates from {templates_path}")
        templates = create_template_registry(templates_path)
        print(f"✓ Loaded {len(templates)} templates")
        
        # Load data with offline resolver
        resolver = OfflineResolver()
        obj_map = ObjectMap(resolver)
        
        print(f"Validating data from {data_dir}")
        load_object_data(data_dir, templates, obj_map)
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
main.add_command(list_templates)
main.add_command(validate)


if __name__ == '__main__':
    sys.exit(main())

# The end.