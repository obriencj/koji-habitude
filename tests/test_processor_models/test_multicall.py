"""
Verifying our shared multicall mocking infrastructure works.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated

from unittest import TestCase
from . import MulticallMocking


class TestMulticallMocking(MulticallMocking, TestCase):

    def test_multicall_response_queue(self):
        """
        Test that multicall responses can be queued and returned correctly.

        This demonstrates how to use the new multicall response queue functionality
        to easily mock koji multicall operations.
        """
        # Queue up responses for specific methods
        self.queue_client_response('getTag', {'name': 'test-tag', 'arches': 'x86_64'})
        self.queue_client_response('listTargets', [
            {'name': 'target1', 'build_tag': 'build-tag1'},
            {'name': 'target2', 'build_tag': 'build-tag2'}
        ])

        # Queue a callable response that can use parameters
        def dynamic_response(*args, **kwargs):
            return {'method': 'getTag', 'args': args, 'kwargs': kwargs}
        self.queue_client_response('getTagInfo', dynamic_response)

        # Verify the queue is set up correctly
        self.assertIn('getTag', self.client_responses)
        self.assertIn('listTargets', self.client_responses)
        self.assertIn('getTagInfo', self.client_responses)

        # Test that responses are consumed in order
        result1 = self.client_callmethod_mock('getTag', 'test-tag')
        self.assertEqual(result1, {'name': 'test-tag', 'arches': 'x86_64'})

        result2 = self.client_callmethod_mock('listTargets')
        self.assertEqual(result2, [
            {'name': 'target1', 'build_tag': 'build-tag1'},
            {'name': 'target2', 'build_tag': 'build-tag2'}
        ])

        result3 = self.client_callmethod_mock('getTagInfo', 'test-tag', extra='param')
        self.assertEqual(result3, {'method': 'getTag', 'args': ('test-tag',), 'kwargs': {'extra': 'param'}})


    def test_multicall_execution_with_queued_responses(self):
        """
        Test that multicall execution properly uses queued responses.

        This demonstrates the actual multicall behavior where:
        1. Individual calls are recorded during multicall context
        2. When context exits, all calls are sent as a batch to multiCall
        3. Our mock processes the batch and returns the queued responses
        """
        # Queue up responses for the multicall
        self.queue_client_response('getTag', {'name': 'test-tag', 'arches': 'x86_64'})
        self.queue_client_response('listTargets', [
            {'name': 'target1', 'build_tag': 'build-tag1'},
            {'name': 'target2', 'build_tag': 'build-tag2'}
        ])
        self.queue_client_response('getTag', {'name': 'test-tag', 'arches': 'x86_64'})  # Second call

        # Simulate a multicall execution by calling the mock directly
        # This simulates what happens when the multicall context exits
        calls = [
            {'methodName': 'getTag', 'params': ('test-tag',)},
            {'methodName': 'listTargets', 'params': ()},
            {'methodName': 'getTag', 'params': ('another-tag',)}
        ]

        # Call the client mock with the batch of calls
        # The multicall format is multiCall((calls,), {}) where calls is a list
        results = self.client_callmethod_mock('multiCall', (calls,), {})

        # Verify we got the expected number of results
        self.assertEqual(len(results), 3)

        # Verify the first getTag call returned our queued response
        self.assertEqual(results[0], [{'name': 'test-tag', 'arches': 'x86_64'}])

        # Verify the listTargets call returned our queued response
        self.assertEqual(results[1], [[
            {'name': 'target1', 'build_tag': 'build-tag1'},
            {'name': 'target2', 'build_tag': 'build-tag2'}
        ]])

        # Verify the second getTag call also returned our queued response
        self.assertEqual(results[2], [{'name': 'test-tag', 'arches': 'x86_64'}])


    def test_multicall_individual_calls(self):
        """
        Test that individual calls during multicall context work correctly.

        This tests the case where individual method calls are made during
        the multicall context, which should return the actual response data.
        """
        # Queue up responses for the multicall
        self.queue_client_response('getBuildTarget', {'name': 'test-target', 'build_tag_name': 'build-tag'})
        self.queue_client_response('getBuildTarget', {'name': 'another-target', 'build_tag_name': 'build-tag'})

        # Simulate individual calls during multicall context
        result1 = self.client_callmethod_mock('getBuildTarget', 'test-target')
        result2 = self.client_callmethod_mock('getBuildTarget', 'another-target')

        # Verify we got the expected responses
        self.assertIsNotNone(result1)
        self.assertIsNotNone(result2)

        # Verify the responses are correct
        self.assertEqual(result1, {'name': 'test-target', 'build_tag_name': 'build-tag'})
        self.assertEqual(result2, {'name': 'another-target', 'build_tag_name': 'build-tag'})


# The end.
