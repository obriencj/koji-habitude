"""
koji-habitude - koji_client

Koji interaction wrapper with multicall support for efficient batch operations.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from typing import Dict, List, Optional, Any, Tuple
import koji

from .models.base import BaseKojiObject
from .resolver import ObjectTier


class KojiClient:
    """
    Wrapper for koji client with multicall support.
    """
    
    def __init__(self, koji_profile: Optional[str] = None):
        """
        Initialize koji client.
        
        Args:
            koji_profile: Koji profile to use, None for default
        """
        
        self.koji_profile = koji_profile
        self.session = None
        
    def connect(self) -> None:
        """
        Establish connection to koji hub.
        """
        
        if self.koji_profile:
            # Use specific profile
            self.session = koji.get_profile_session(self.koji_profile)
        else:
            # Use default profile
            self.session = koji.get_profile_session()
            
        # Activate session if authentication is needed
        if hasattr(self.session, 'krb_login'):
            try:
                self.session.krb_login()
            except Exception:
                # Authentication may not be required for read operations
                pass
                
    def disconnect(self) -> None:
        """
        Close koji session.
        """
        
        if self.session:
            self.session.logout()
            self.session = None
            
    def __enter__(self):
        """
        Context manager entry.
        """
        
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit.
        """
        
        self.disconnect()
        
    def query_objects_multicall(self, objects: List[BaseKojiObject]) -> Dict[Tuple[str, str], Optional[Dict[str, Any]]]:
        """
        Query koji for current state of objects using multicall.
        
        Args:
            objects: List of objects to query
            
        Returns:
            Dictionary mapping object keys to their koji data (or None if not found)
        """
        
        if not self.session:
            raise RuntimeError("Not connected to koji")
            
        if not objects:
            return {}
            
        # Group objects by type for efficient querying
        queries_by_type = {}
        for obj in objects:
            if obj.type not in queries_by_type:
                queries_by_type[obj.type] = []
            queries_by_type[obj.type].append(obj)
            
        # Build multicall queries
        multicall = koji.MultiCallSession(self.session)
        call_map = {}  # Maps call index to object key
        
        call_index = 0
        for obj_type, type_objects in queries_by_type.items():
            for obj in type_objects:
                # Add appropriate koji query based on object type
                if obj_type == 'tag':
                    multicall.getTag(obj.name)
                elif obj_type == 'external-repo':
                    multicall.getExternalRepo(obj.name)
                elif obj_type == 'user':
                    multicall.getUser(obj.name)
                elif obj_type == 'target':
                    multicall.getBuildTarget(obj.name)
                elif obj_type == 'host':
                    multicall.getHost(obj.name)
                elif obj_type == 'group':
                    multicall.getTagGroups(tag=obj.data.get('tag'), inherit=False)
                else:
                    # Skip unknown types
                    continue
                    
                call_map[call_index] = obj.key
                call_index += 1
                
        # Execute multicall
        if not call_map:
            return {}
            
        results = multicall()
        
        # Process results
        koji_data = {}
        for idx, result in enumerate(results):
            if idx in call_map:
                obj_key = call_map[idx]
                
                if isinstance(result, dict) and 'faultCode' in result:
                    # Error occurred
                    koji_data[obj_key] = None
                elif isinstance(result, list) and len(result) == 2:
                    # Standard multicall result format
                    koji_data[obj_key] = result[0] if result[0] else None
                else:
                    # Direct result
                    koji_data[obj_key] = result if result else None
                    
        return koji_data
        
    def apply_updates_multicall(self, updates: List[Dict[str, Any]]) -> List[Any]:
        """
        Apply updates to koji using multicall.
        
        Args:
            updates: List of koji API call dictionaries
            
        Returns:
            List of results from the multicall
        """
        
        if not self.session:
            raise RuntimeError("Not connected to koji")
            
        if not updates:
            return []
            
        # Build multicall with updates
        multicall = koji.MultiCallSession(self.session)
        
        for update in updates:
            method = update.get('method')
            args = update.get('args', [])
            kwargs = update.get('kwargs', {})
            
            if not method:
                continue
                
            # Add call to multicall
            getattr(multicall, method)(*args, **kwargs)
            
        # Execute multicall
        results = multicall()
        return results
        
    def process_object_tier(self, tier: ObjectTier) -> None:
        """
        Process a complete object tier against koji.
        
        This queries koji for current state, computes diffs, and applies updates.
        
        Args:
            tier: ObjectTier to process
        """
        
        if not tier:
            return
            
        objects = list(tier)
        print(f"Processing tier with {len(objects)} objects")
        
        # Query current state from koji
        koji_data = self.query_objects_multicall(objects)
        
        # Collect all updates needed
        all_updates = []
        for obj in objects:
            current_data = koji_data.get(obj.key)
            updates = obj.koji_diff(current_data)
            all_updates.extend(updates)
            
        # Apply updates if any
        if all_updates:
            print(f"Applying {len(all_updates)} updates")
            try:
                results = self.apply_updates_multicall(all_updates)
                print(f"Updates completed: {len(results)} results")
            except Exception as e:
                print(f"Error applying updates: {e}")
        else:
            print("No updates needed")
            
    def verify_object_exists(self, obj_type: str, obj_name: str) -> bool:
        """
        Verify that an object exists in koji.
        
        Args:
            obj_type: Type of object to check
            obj_name: Name of object to check
            
        Returns:
            True if object exists in koji
        """
        
        if not self.session:
            raise RuntimeError("Not connected to koji")
            
        try:
            if obj_type == 'tag':
                result = self.session.getTag(obj_name)
            elif obj_type == 'external-repo':
                result = self.session.getExternalRepo(obj_name)
            elif obj_type == 'user':
                result = self.session.getUser(obj_name)
            elif obj_type == 'target':
                result = self.session.getBuildTarget(obj_name)
            elif obj_type == 'host':
                result = self.session.getHost(obj_name)
            elif obj_type == 'group':
                # Groups are more complex, just return True for now
                return True
            else:
                return False
                
            return result is not None
            
        except Exception:
            return False


def create_koji_client(koji_profile: Optional[str] = None) -> KojiClient:
    """
    Create and return a koji client.
    
    Args:
        koji_profile: Optional koji profile to use
        
    Returns:
        Configured KojiClient instance
    """
    
    return KojiClient(koji_profile)

# The end.