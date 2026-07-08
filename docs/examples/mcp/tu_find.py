from tooluniverse import ToolUniverse

# Initialize ToolUniverse
tu = ToolUniverse()
# Load tool finder tools
tu.load_tools()
# if you want to load a subset of tools, `tool_finder` must be included in the list of tool types
# tu.load_tools(tool_type=["tool_finder", ...other tool types...])

# Use keyword search
result = tu.run({
    "name": "Tool_Finder_Keyword",
    "arguments": {
        "description": "astronomy research tool",
        "limit": 10
    }
})
print(result)