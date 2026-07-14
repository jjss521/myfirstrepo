from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class ProjectType(Base):
    """工程类型"""
    __tablename__ = 'project_types'

    id = Column(Integer, primary_key=True)
    code = Column(String(30), unique=True, nullable=False, comment='工程类型代码')
    name = Column(String(50), nullable=False, comment='工程类型名称')
    design_stage = Column(String(20), nullable=False, comment='设计阶段：可研/初步设计/施工图')
    description = Column(Text, comment='备注')
    created_at = Column(DateTime, default=datetime.now)

    sections = relationship('Section', back_populates='project_type', cascade='all, delete-orphan')
    templates = relationship('Template', back_populates='project_type', cascade='all, delete-orphan')
    documents = relationship('Document', back_populates='project_type', cascade='all, delete-orphan')


class Section(Base):
    """深度要求栏目"""
    __tablename__ = 'sections'

    id = Column(Integer, primary_key=True)
    project_type_id = Column(Integer, ForeignKey('project_types.id'), nullable=False)
    category = Column(String(50), nullable=False, comment='电气设计 / 仪表自控设计 / 照明工程 等')
    section_order = Column(Integer, nullable=False, comment='栏目序号')
    title = Column(String(100), nullable=False, comment='栏目名称')
    depth_requirement = Column(Text, nullable=False, comment='深度要求')
    default_content = Column(Text, comment='默认模板内容')
    has_calculation = Column(Boolean, default=False, comment='是否涉及计算')
    table_required = Column(Boolean, default=False, comment='是否需表格')
    calc_from_excel = Column(Boolean, default=False, comment='是否从Excel获取计算数据')
    is_required = Column(Boolean, default=True, comment='必填')
    optional = Column(Boolean, default=False, comment='是否可选栏目')

    project_type = relationship('ProjectType', back_populates='sections')


class Template(Base):
    """模板"""
    __tablename__ = 'templates'

    id = Column(Integer, primary_key=True)
    project_type_id = Column(Integer, ForeignKey('project_types.id'), nullable=False)
    name = Column(String(100), nullable=False)
    content_type = Column(String(20), comment='电气说明 / 自控说明 / 设备材料表')
    source_doc = Column(String(500), comment='来源文档路径')
    full_text = Column(Text, comment='全文内容')
    sections_map = Column(JSON, comment='栏目内容映射 {section_id: content}')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    project_type = relationship('ProjectType', back_populates='templates')


class Document(Base):
    """上传的参考文档"""
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    project_type_id = Column(Integer, ForeignKey('project_types.id'))
    name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    doc_type = Column(String(20), comment='可研文本 / 初设文本 / 负荷计算书 / 其他')
    design_stage = Column(String(20), comment='设计阶段')
    file_ext = Column(String(10))
    file_size = Column(Integer)
    tags = Column(JSON, comment='标签')
    uploaded_at = Column(DateTime, default=datetime.now)

    project_type = relationship('ProjectType', back_populates='documents')


class GenerationLog(Base):
    """生成记录"""
    __tablename__ = 'generation_logs'

    id = Column(Integer, primary_key=True)
    project_type_id = Column(Integer, ForeignKey('project_types.id'))
    design_stage = Column(String(20))
    input_file = Column(String(500), comment='输入的负荷计算书')
    output_file = Column(String(500), comment='输出文件路径')
    generation_params = Column(JSON, comment='生成参数')
    excel_data = Column(JSON, comment='解析后的Excel数据摘要')
    generated_at = Column(DateTime, default=datetime.now)
    status = Column(String(20), default='success')
    error_msg = Column(Text)
