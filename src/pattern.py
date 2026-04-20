from dataclasses import dataclass
from typing import List, Union, Any
import copy
import re

@dataclass
@dataclass
class Event:
    timestamp: float # Start time in cycles (0.0 to 1.0 for one cycle)
    duration: float  # Duration in cycles
    value: Any       # The note (e.g., "c4", "60", etc.)
    priority: int = 0
    waveform: str = "sine"
    volume: float = 1.0

class Pattern:
    def __init__(self, events: List[Event] = None, cycles=1, operator=None, operands=None):
        self.events = events or []
        self.cycles = cycles
        self.operator = operator # "mul" etc
        self.operands = operands or [] # List of Patterns
        
    def s(self, waveform: str):
        """Set the waveform for all events in the pattern."""
        new_events = []
        for e in self.events:
            ev = copy.deepcopy(e)
            ev.waveform = waveform
            new_events.append(ev)
        return Pattern(new_events, self.cycles)
        
    def amp(self, volume: float):
        """Set volume (amplitude) for all events."""
        new_events = []
        for e in self.events:
            ev = copy.deepcopy(e)
            ev.volume = volume
            new_events.append(ev)
        return Pattern(new_events, self.cycles)

    # ... (existing methods)

    def __sub__(self, other):
        """Subtract pattern (add inverted phase) using - operator."""
        if not isinstance(other, Pattern):
            return NotImplemented
            
        # P1 - P2 = P1 + (P2 * -1)
        
        # Copy self events
        new_events = [copy.deepcopy(e) for e in self.events]
        
        # Invert volume of other events
        for e in other.events:
            ev = copy.deepcopy(e)
            ev.volume *= -1.0 # Invert phase
            new_events.append(ev)
            
        new_cycles = max(self.cycles, other.cycles)
        return Pattern(new_events, new_cycles)

    @staticmethod
    def from_string(s: str) -> 'Pattern':
        """
        Parses a simple mini-notation string.
        Supported: "a b c" (sequential), "[a b] c" (subdivision)
        """
        # Very basic parser for MVP. 
        # Tokenize by spaces, keeping brackets.
        # This is a naive implementation; a real one needs a recursive descent parser.
        
        # Pre-process to handle brackets with spaces
        # Note: This is a placeholder for a complex parser. 
        # For now, we will handle a single level of nesting manually or use a simple recursive approach logic.
        
        tokens = Pattern._tokenize(s)
        events = Pattern._parse_tokens(tokens, 0, 1)
        return Pattern(events)

    @staticmethod
    def _tokenize(s: str):
        # Insert spaces around brackets to make splitting easier
        s = s.replace('[', ' [ ').replace(']', ' ] ')
        return s.split()

    @staticmethod
    def _parse_tokens(tokens, start_time, duration):
        events = []
        if not tokens:
            return events

        # Group tokens into "steps"
        steps = []
        current_step = []
        depth = 0
        
        for token in tokens:
            if token == '[':
                if depth > 0:
                    current_step.append(token)
                depth += 1
            elif token == ']':
                depth -= 1
                if depth > 0:
                    current_step.append(token)
                else:
                    # End of a group
                    steps.append(current_step)
                    current_step = []
            else:
                if depth > 0:
                    current_step.append(token)
                else:
                    steps.append(token)
        
        # Now process each step
        step_duration = duration / len(steps)
        current_time = start_time
        
        for step in steps:
            if isinstance(step, list):
                # Recursive case: it's a sub-pattern
                events.extend(Pattern._parse_tokens(step, current_time, step_duration))
            else:
                # Base case: note
                if step != "~": # ~ is rest
                    events.append(Event(current_time, step_duration, step))
            current_time += step_duration
            
        return events

    def note(self, note_str: str):
        # Override or create pattern from string
        # If self is empty, create from string. If self has events, maybe mod them?
        # Strudel usually works by chaining: note("...").s("...")
        # For this Python port, let's say Strudel() factory creates an empty implementation,
        # but usually you start with sequences.
        pass

    def fast(self, n: float):
        """Speed up the pattern by n."""
        new_events = []
        for e in self.events:
            new_e = copy.deepcopy(e)
            new_e.timestamp /= n
            new_e.duration /= n
            new_events.append(new_e)
        return Pattern(new_events, self.cycles)
    
    # Enable chaining for new patterns usually
    def get_events(self):
        return sorted(self.events, key=lambda e: e.timestamp)

    def times(self, n):
        """Repeat the pattern n times."""
        new_events = []
        for i in range(n):
            offset = i * self.cycles # Assuming 1 cycle length usually? 
            # Actually Strudel cycles are abstract. 
            # In our audio engine, we will map 1 cycle = X seconds (bpm).
            for e in self.events:
                ev = copy.deepcopy(e)
                ev.timestamp += i # Add cycle index to timestamp
                new_events.append(ev)
        return Pattern(new_events, self.cycles * n)

    def __add__(self, other):
        """Layer two patterns together (polyphony)."""
        if not isinstance(other, Pattern):
            return NotImplemented
            
        # New cycle length
        new_cycles = max(self.cycles, other.cycles)

        # Optimization: If both are simple event sequences, merge them
        if self.operator is None and other.operator is None:
            new_events = self.events + other.events
            return Pattern(new_events, new_cycles)
        
        # Otherwise, use recursive 'add' operator
        return Pattern(cycles=new_cycles, operator="add", operands=[self, other])

    def __and__(self, other):
        """Concatenate patterns (play one after another) using & operator."""
        if not isinstance(other, Pattern):
            return NotImplemented
            
        new_cycles = self.cycles + other.cycles

        # Optimization: If both are simple event sequences, merge with offset
        if self.operator is None and other.operator is None:
            new_events = [copy.deepcopy(e) for e in self.events]
            offset = self.cycles
            for e in other.events:
                ev = copy.deepcopy(e)
                ev.timestamp += offset
                new_events.append(ev)
            return Pattern(new_events, new_cycles)
            
        # Otherwise, use recursive 'concat' operator
        return Pattern(cycles=new_cycles, operator="concat", operands=[self, other])

    def __mul__(self, other):
        """Multiply two patterns (Ring Modulation) or Pattern * Scalar (Volume)."""
        if isinstance(other, (int, float)):
            # Volume scaling
            return Pattern(cycles=self.cycles, operator="mul", operands=[self, other])
        elif isinstance(other, Pattern):
            # Ring modulation
            new_cycles = max(self.cycles, other.cycles)
            return Pattern(cycles=new_cycles, operator="mul", operands=[self, other])
        else:
            return NotImplemented
            
        # Recursive structure
    def reverse(self):
        """Reverse the pattern (audio reverse)."""
        # This is a recursive operator that will be handled by the renderer.
        # It means "Render self, then reverse the buffer".
        return Pattern(cycles=self.cycles, operator="reverse", operands=[self])
