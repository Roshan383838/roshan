import json
from pydantic import BaseModel, ValidationError

# --- Task 1: Registry and Dispatch ---

tool_registry = {
    "get_stock": get_stock,
    "calculate_total": calculate_total
}

def execute_tool(tool_name: str, arguments: dict):
    if tool_name not in tool_registry:
        raise ValueError(f"Tool '{tool_name}' is not registered.")
    tool_func = tool_registry[tool_name]
    return tool_func(**arguments)


# --- Task 2: Validation ---

class GetStockSchema(BaseModel):
    item: str

class CalculateTotalSchema(BaseModel):
    price_per_unit: float
    quantity: float

def validate_arguments(tool_name: str, arguments: dict):
    try:
        if tool_name == "get_stock":
            GetStockSchema(**arguments)
        elif tool_name == "calculate_total":
            CalculateTotalSchema(**arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
        return None
    except (ValidationError, Exception) as e:
        return {"error": str(e)}


# --- Task 3: Agent Loop ---

def run_agent(user_message: str, model, max_iterations: int = 3):
    messages = [{"role": "user", "content": user_message}]
    trace = []
    
    for _ in range(max_iterations):
        response = model(messages)
        trace.append(f"Model call: {response}")
        
        tool_calls = response.get("tool_calls", [])
        if not tool_calls:
            messages.append(response)
            return response.get("content"), trace
        
        messages.append(response)
        
        for tool_call in tool_calls:
            call_id = tool_call.get("id")
            name = tool_call.get("name")
            arguments = tool_call.get("arguments", {})
            
            validation_error = validate_arguments(name, arguments)
            if validation_error is not None:
                result = validation_error
                trace.append(f"Tool call rejected: {name} with args {arguments}. Error: {validation_error}")
            else:
                try:
                    result = execute_tool(name, arguments)
                    trace.append(f"Tool call executed: {name} with args {arguments}. Result: {result}")
                except Exception as e:
                    result = {"error": str(e)}
                    trace.append(f"Tool call failed: {name} with args {arguments}. Error: {str(e)}")
            
            messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": json.dumps(result)
            })
            
    trace.append("Maximum iterations reached")
    return "Maximum iterations reached", trace