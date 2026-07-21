# -*- coding: utf-8 -*-
"""数据库 ORM 模型。"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime
from datetime import datetime

from .database import Base


class ProjectType(Base):
    __tablename__ = 'project_types'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, index=True)        # 如 water_supply_preliminary
    name = Column(String(64))                                  # 给水工程
    design_stage = Column(String(32))                          # 初步设计 / 可研
    description = Column(Text)                                 # 规范出处


class Section(Base):
    __tablename__ = 'sections'
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_type_id = Column(Integer, ForeignKey('project_types.id'))
    category = Column(String(64))                              # 电气设计 / 仪表自控弱电设计
    section_order = Column(Integer)
    title = Column(String(128))
    depth_requirement = Column(Text)
    has_calculation = Column(Boolean, default=False)
    table_required = Column(Boolean, default=False)
    calc_from_excel = Column(Boolean, default=False)
    is_required = Column(Boolean, default=True)
    optional = Column(Boolean, default=False)


class Template(Base):
    __tablename__ = 'templates'
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_type = Column(String(64))                          # water_supply
    design_stage = Column(String(32))
    category = Column(String(64))
    title = Column(String(128))
    content = Column(Text)
    updated_at = Column(DateTime, default=datetime.now)


class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255))
    original_name = Column(String(255))
    doc_type = Column(String(32))                              # reference / load_excel
    project_type = Column(String(64))
    design_stage = Column(String(32))
    uploaded_at = Column(DateTime, default=datetime.now)
    note = Column(Text)


class GenerationLog(Base):
    __tablename__ = 'generation_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_name = Column(String(255))
    project_type = Column(String(64))
    design_stage = Column(String(32))
    template = Column(String(32))
    excel_path = Column(String(512))
    output_path = Column(String(512))
    created_at = Column(DateTime, default=datetime.now)
