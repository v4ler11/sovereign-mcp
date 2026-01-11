import re

from typing import Dict, Any, Literal, List, Union, Awaitable, Callable, AsyncIterator

from pydantic import BaseModel, Field, field_validator

from mcp.schemas.common import Icon, Annotations
from mcp.schemas.resources import ResourceDataText, ResourceDataBinary


class ToolResultText(BaseModel):
    type: Literal["text"] = "text"
    text: str
    annotations: Annotations | None = None


class ToolResultImage(BaseModel):
    type: Literal["image"] = "image"
    data: str
    mimeType: str
    annotations: Annotations | None = None


class ToolResultAudio(BaseModel):
    type: Literal["audio"] = "audio"
    data: str
    mimeType: str
    annotations: Annotations | None = None


class ToolResultResource(BaseModel):
    type: Literal["resource"] = "resource"
    resource: Union[ResourceDataText, ResourceDataBinary]
    annotations: Annotations | None = None


class ToolResultResourceLink(BaseModel):
    type: Literal["resource_link"] = "resource_link"
    uri: str
    name: str
    description: str | None = None
    mimeType: str
    annotations: Annotations | None = None


ToolContent = Union[
    ToolResultText,
    ToolResultImage,
    ToolResultAudio,
    ToolResultResource,
    ToolResultResourceLink
]


class ToolDefinition(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    title: str | None = None
    description: str
    inputSchema: Dict[str, Any]
    outputSchema: Dict[str, Any] | None = None
    icons: List[Icon] | None = None

    @classmethod
    @field_validator('name')
    def validate_name(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_.-]+$', v):
            raise ValueError(f"Invalid tool name '{v}'")
        return v


class CallToolParams(BaseModel):
    name: str
    arguments: Dict[str, Any]


class ToolsCallResult(BaseModel):
    content: List[ToolContent] = Field(default_factory=list)
    structuredContent: Dict[str, Any] | None = None
    isError: bool = False


class ToolsListResponseResult(BaseModel):
    tools: List[ToolDefinition]
    nextCursor: str | None = None


class ToolsResponse(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: Union[str, int]
    result: Union[ToolsListResponseResult, ToolsCallResult]


class ToolsChangedNotification(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    method: Literal["notifications/tools/list_changed"] = "notifications/tools/list_changed"


class ToolProgress(BaseModel):
    progress: float = Field(..., ge=0.0)
    total: float | None = Field(default=None, ge=0.0)
    message: str | None = None


class ToolResult(BaseModel):
    content: List[ToolContent]
    structuredContent: Dict[str, Any] | None = None
    isError: bool = False


class Tool(BaseModel):
    """
    Server-side representation of a registered tool.
    """
    func: Callable[
        [Dict[str, Any]],
        Union[
            Awaitable[ToolResult],
            AsyncIterator[Union[ToolProgress, ToolResult]]
        ]
    ]
    definition: ToolDefinition
    timeout: int = 60
