import ast
import ollama
from typing import List, Dict, Any
from enum import Enum, auto

class Operation(str, Enum):
    """Available mathematical operations"""
    ADD = "add"
    MULTIPLY = "multiply"
    AVERAGE = "average"

def get_current_weather(location: str, unit: str = "celsius") -> Dict[str, Any]:
    """Get the current weather in a given location
    
    Args:
        location: The city and state, e.g. San Francisco, CA
        unit: The temperature unit to use (celsius or fahrenheit)
    
    Returns:
        dict: Weather information including location, temperature, unit, and forecast
    """
    return {
        "location": location,
        "temperature": 22,
        "unit": unit,
        "forecast": "sunny"
    }

def calculate(operation: Operation, numbers: List[float]) -> float:
    """Perform mathematical calculations
    
    Args:
        operation: The mathematical operation to perform (one of: add, multiply, average)
        numbers: List of numbers to perform the operation on
    
    Returns:
        float: Result of the mathematical operation
    """
    # Convert list of numbers in string (as a string) into a list of floats
    def string_to_float_list(s):
        try:
            return [float(x) for x in ast.literal_eval(s)]
        except (ValueError, SyntaxError):
            raise ValueError("Invalid input format")

    numbers = string_to_float_list(numbers)
    
    if operation == Operation.ADD:
        return sum(numbers)
    elif operation == Operation.MULTIPLY:
        result = 1
        for num in numbers:
            result *= num
        return result
    elif operation == Operation.AVERAGE:
        return sum(numbers) / len(numbers)
    else:
        raise ValueError(f"Unknown operation: {operation}")

def main():
    # Test prompts that should trigger function calls
    test_prompts = [
        "What's the weather like in London?",
        "Can you calculate the average of these numbers: 10, 15, 20, 25?",
        "What's the sum of 5, 10, 15, and 20?",
        "What's the weather in Tokyo in fahrenheit?",
        "Please multiply these numbers: 2, 3, 4, 5",
        "Tell me the current temperature in Paris in celsius"
    ]
    
    print("Testing Ollama with function calling capabilities...")
    print("Available functions:", ", ".join([get_current_weather.__name__, calculate.__name__]))
    print("=" * 70)
    
    # Create a dictionary of available functions
    available_functions = {
        'get_current_weather': get_current_weather,
        'calculate': calculate
    }
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\nTest {i}: {prompt}")
        print("-" * 70)
        
        # Call Ollama with the functions as tools
        response = ollama.chat(
            model='llama3.1',
            messages=[{'role': 'user', 'content': prompt}],
            tools=[get_current_weather, calculate]
        )
        
        # Process any tool calls
        for tool in response.message.tool_calls or []:
            function_to_call = available_functions.get(tool.function.name)
            if function_to_call:
                result = function_to_call(**tool.function.arguments)
                print(f"\nFunction called: {tool.function.name}")
                print(f"Arguments: {tool.function.arguments}")
                print(f"Result: {result}\n")
        
        # Print the model's response
        print(response.message.content)
        print("-" * 70)

if __name__ == "__main__":
    main() 