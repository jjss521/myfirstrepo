from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# === 工程类型 ===
class ProjectTypeBase(BaseModel):
    code: str
    name: str
    design_stage: str = '初步设计'

class ProjectTypeCreate(ProjectTypeBase):
    pass

class ProjectTypeOut(ProjectTypeBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


# === 栏目 ===
class SectionBase(BaseModel):
    project_type_id: int
    category: str
    section_order: int
    title: str
    depth_requirement: str
    default_content: Optional[str] = None
    has_calculation: bool = False
    table_required: bool = False
    calc_from_excel: bool = False
    is_required: bool = True
    optional: bool = False

class SectionCreate(SectionBase):
    pass

class SectionOut(SectionBase):
    id: int
    class Config:
        from_attributes = True


# === 模板 ===
class TemplateBase(BaseModel):
    project_type_id: int
    name: str
    content_type: Optional[str] = None
    source_doc: Optional[str] = None
    full_text: Optional[str] = None
    sections_map: Optional[dict] = None

class TemplateCreate(TemplateBase):
    pass

class TemplateOut(TemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


# === 文档 ===
class DocumentOut(BaseModel):
    id: int
    name: str
    file_path: str
    doc_type: Optional[str] = None
    design_stage: Optional[str] = None
    file_ext: Optional[str] = None
    file_size: Optional[int] = None
    tags: Optional[Any] = None
    project_type_id: Optional[int] = None
    uploaded_at: datetime
    class Config:
        from_attributes = True


# === 生成请求 ===
class GenerateRequest(BaseModel):
    excel_path: str = Field(..., description='负荷计算Excel文件路径')
    project_type: str = Field(..., description='工程类型: water_supply/drainage/road/sanitation')
    design_stage: str = Field('初步设计', description='设计阶段: 可研/初步设计/施工图')
    project_name: Optional[str] = Field(None, description='项目名称')
    voltage_level: Optional[str] = Field('10kV', description='供电电压等级')
    standby_power: Optional[str] = Field(None, description='备用电源说明')
    load_level: Optional[str] = Field('二级', description='负荷等级')


class GenerateResponse(BaseModel):
    success: bool
    output_path: Optional[str] = None
    excel_summary: Optional[dict] = None
    message: Optional[str] = None
    error: Optional[str] = None
