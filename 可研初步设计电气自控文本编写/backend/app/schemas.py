# -*- coding: utf-8 -*-
"""Pydantic 请求/响应模型。"""
from pydantic import BaseModel
from typing import Optional, List


class GenerateRequest(BaseModel):
    excel_path: str
    project_type: str                       # water_supply / drainage / road / sanitation
    design_stage: str = '初步设计'
    project_name: str = '新建项目'
    voltage_level: str = '10kV'
    load_level: str = '二级'
    power_source: str = '两路'
    standby_desc: str = ''
    template: str = 'standard'


class GenerateResponse(BaseModel):
    output_path: str
    project_name: str
    project_type: str
    design_stage: str
    template: str
    summary: dict


class ProjectTypeOut(BaseModel):
    id: int
    code: str
    name: str
    design_stage: str
    description: str


class SectionOut(BaseModel):
    id: int
    project_type_id: int
    category: str
    section_order: int
    title: str
    depth_requirement: str
    has_calculation: bool
    table_required: bool
    calc_from_excel: bool
    optional: bool


class UploadResponse(BaseModel):
    id: int
    filename: str
    original_name: str
    doc_type: str
