"""
koji-habitude - models.tag

Tag model for koji tag objects with inheritance and external repo dependencies.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from typing import Dict, List, Tuple, Any
from .base import BaseKojiObject


class Tag(BaseKojiObject):
    """
    Koji tag object model.
    """

    def dependent_keys(self) -> List[Tuple[str, str]]:
        """
        Return dependencies for this tag.

        Tags depend on:
        - Parent tags (simple parent field)
        - Parent tags in inheritance chain
        - External repositories
        - Inherit from tags
        """

        deps = []

        # Check for simple parent dependency
        parent = self.data.get('parent')
        if parent:
            deps.append(('tag', parent))

        # Check for inherit_from dependencies
        inherit_from = self.data.get('inherit_from', [])
        if isinstance(inherit_from, list):
            for tag in inherit_from:
                deps.append(('tag', tag))

        # Check for inheritance dependencies
        inheritance = self.data.get('inheritance', [])
        if isinstance(inheritance, list):
            for parent in inheritance:
                if isinstance(parent, dict) and 'parent' in parent:
                    deps.append(('tag', parent['parent']))
                elif isinstance(parent, str):
                    deps.append(('tag', parent))

        # Check for external repo dependencies
        external_repos = self.data.get('external-repos', [])
        if isinstance(external_repos, list):
            for repo in external_repos:
                if isinstance(repo, dict) and 'name' in repo:
                    deps.append(('external-repo', repo['name']))
                elif isinstance(repo, str):
                    deps.append(('external-repo', repo))

        return deps

    def _extract_deferred_data(self, dep_list: List[Tuple[str, str]]) -> Dict[str, Any]:
        """
        Extract inheritance or external-repo data that should be deferred.

        Args:
            dep_list: List of dependency keys being deferred

        Returns:
            Dictionary containing the deferred inheritance/external-repo data
        """

        deferred = {}

        # Find which dependencies to defer
        deferred_tags = {name for dep_type, name in dep_list if dep_type == 'tag'}
        deferred_repos = {name for dep_type, name in dep_list if dep_type == 'external-repo'}

        # Extract deferred inheritance
        inheritance = self.data.get('inheritance', [])
        if inheritance and deferred_tags:
            deferred_inheritance = []
            remaining_inheritance = []

            for parent in inheritance:
                parent_name = parent.get('parent') if isinstance(parent, dict) else parent
                if parent_name in deferred_tags:
                    deferred_inheritance.append(parent)
                else:
                    remaining_inheritance.append(parent)

            if deferred_inheritance:
                deferred['inheritance'] = deferred_inheritance
                self.data['inheritance'] = remaining_inheritance

        # Extract deferred external repos
        external_repos = self.data.get('external-repos', [])
        if external_repos and deferred_repos:
            deferred_ext_repos = []
            remaining_ext_repos = []

            for repo in external_repos:
                repo_name = repo.get('name') if isinstance(repo, dict) else repo
                if repo_name in deferred_repos:
                    deferred_ext_repos.append(repo)
                else:
                    remaining_ext_repos.append(repo)

            if deferred_ext_repos:
                deferred['external-repos'] = deferred_ext_repos
                self.data['external-repos'] = remaining_ext_repos

        return deferred

# The end.