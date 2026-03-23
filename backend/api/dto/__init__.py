"""
DTO (Data Transfer Object) 模块

设计原则:
1. 所有 DTO 继承 BaseDTO
2. 使用 Pydantic 进行验证
3. 自动支持序列化 (to_dict, to_json)
4. 支持从 ORM 模型转换 (from_orm)

使用示例:
    class UserDTO(BaseDTO):
        name: str
        email: str
        
    user = UserDTO(name="test", email="test@example.com")
    data = user.to_dict()  # {"name": "test", "email": "test@example.com"}
"""

from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional, TypeVar, Generic, Type
from datetime import datetime
import json

T = TypeVar('T')


class BaseDTO(BaseModel):
    """
    所有 DTO 的基类
    
    功能:
    - 自动支持 model_dump() 序列化
    - 支持 from_attributes 从 ORM 转换
    - 统一的 to_dict() 和 to_json() 方法
    - 统一的 API 响应格式
    """
    
    model_config = ConfigDict(
        from_attributes=True,      # 支持从 ORM 模型转换
        populate_by_name=True,     # 支持字段别名
        use_enum_values=True,      # 枚举使用值而非枚举对象
        str_strip_whitespace=True, # 自动去除字符串空白
    )
    
    def to_dict(self, exclude_none: bool = True, **kwargs) -> Dict[str, Any]:
        """
        转换为字典
        
        Args:
            exclude_none: 是否排除 None 值
            **kwargs: 传递给 model_dump 的其他参数
            
        Returns:
            Dict[str, Any]: 字典格式的数据
        """
        return self.model_dump(exclude_none=exclude_none, **kwargs)
    
    def to_json(self, exclude_none: bool = True, **kwargs) -> str:
        """
        转换为 JSON 字符串
        
        Args:
            exclude_none: 是否排除 None 值
            **kwargs: 传递给 model_dump_json 的其他参数
            
        Returns:
            str: JSON 字符串
        """
        return self.model_dump_json(exclude_none=exclude_none, **kwargs)
    
    def to_api_response(self, success: bool = True, message: Optional[str] = None) -> Dict[str, Any]:
        """
        转换为统一的 API 响应格式
        
        Returns:
            Dict[str, Any]: 标准化的 API 响应
        """
        response = {
            "success": success,
            "data": self.to_dict()
        }
        if message:
            response["message"] = message
        return response
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        从字典创建实例
        
        Args:
            data: 字典数据
            
        Returns:
            DTO 实例
        """
        return cls.model_validate(data)
    
    @classmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """
        从 JSON 字符串创建实例
        
        Args:
            json_str: JSON 字符串
            
        Returns:
            DTO 实例
        """
        return cls.model_validate_json(json_str)


class ListDTO(BaseDTO, Generic[T]):
    """
    列表响应 DTO 基类
    
    使用示例:
        class UserListDTO(ListDTO[UserDTO]):
            pass
            
        response = UserListDTO(items=[...], total=100, page=1, page_size=20)
    """
    items: list
    total: int = 0
    page: int = 1
    page_size: int = 20
    
    @property
    def has_more(self) -> bool:
        """是否有更多数据"""
        return self.total > self.page * self.page_size
    
    @property
    def total_pages(self) -> int:
        """总页数"""
        return (self.total + self.page_size - 1) // self.page_size


class ErrorResponse(BaseDTO):
    """错误响应 DTO"""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = None
    
    def __init__(self, **data):
        if 'timestamp' not in data or data['timestamp'] is None:
            data['timestamp'] = datetime.now()
        super().__init__(**data)


class MessageResponse(BaseDTO):
    """消息响应 DTO"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


# ==================== 具体业务 DTO ====================

class DirectorStatusDTO(BaseDTO):
    """导播状态 DTO"""
    is_running: bool = False
    current_content: Optional[str] = None
    content_queue: list = []
    uptime: float = 0.0


class ContentItemDTO(BaseDTO):
    """内容项 DTO"""
    type: str
    name: str
    title: str
    path: str
    duration: int = 0
    artist: Optional[str] = None


class PlatformDTO(BaseDTO):
    """平台配置 DTO"""
    platform_type: str
    display_name: str
    enabled: bool = False
    configured: bool = False
    status: str = "disconnected"
    has_stream_key: bool = False
    rtmp_url: str = ""
    last_error: Optional[str] = None


class StreamStatusDTO(BaseDTO):
    """推流状态 DTO"""
    status: str = "idle"
    start_time: Optional[float] = None
    duration: float = 0.0
    frames_sent: int = 0
    bitrate: str = "0"
    error_message: Optional[str] = None
    current_content: Optional[str] = None
